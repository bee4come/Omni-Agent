"""
Payment Client - Refactored Version

Changes:
1. No longer holds TREASURY_PRIVATE_KEY
2. Calls Guardian Service via HTTP to execute payments
3. Retains all policy checking and accounting logic

Call Flow:
1. Policy check (PolicyEngine)
2. Guardian Quote (pre-check)
3. Guardian Pay (actual payment)
4. Call service provider
5. Record usage
"""

import os
import json
import hashlib
import httpx
from typing import Dict, Any, Optional
from pydantic import BaseModel
from dotenv import load_dotenv
from datetime import datetime, date

load_dotenv()

# Guardian Service address (internal service)
GUARDIAN_URL = os.getenv("GUARDIAN_URL", "http://localhost:8100")

class PaymentResult(BaseModel):
    success: bool
    payment_id: str = ""
    tx_hash: str = ""
    service_call_hash: str = ""
    amount: float = 0.0
    error: str = ""
    risk_level: str = "RISK_OK"
    policy_action: str = "ALLOW"

class PaymentClient:
    """
    Refactored Payment Client - does not hold private keys

    All signing operations are delegated to Guardian Service
    """

    def __init__(self, policy_engine=None):
        self.policy_engine = policy_engine

        # Usage tracking
        self.usage_records = []
        self.daily_spending = {}

        # Guardian connection check
        try:
            response = httpx.get(f"{GUARDIAN_URL}/", timeout=5.0)
            if response.status_code == 200:
                print(f"[PAYMENT_CLIENT] Connected to Guardian at {GUARDIAN_URL}")
            else:
                print(f"[PAYMENT_CLIENT] Guardian responded with status {response.status_code}")
        except Exception as e:
            print(f"[PAYMENT_CLIENT] Failed to connect to Guardian: {e}")
            print(f"[PAYMENT_CLIENT] Make sure Guardian Service is running at {GUARDIAN_URL}")

    def build_service_call_hash(self, service_id: str, agent_id: str, task_id: str, payload_dict: Dict[str, Any]) -> str:
        """
        Compute deterministic hash for service invocation

        This hash binds:
        - service_id: which service
        - agent_id: which Agent is calling
        - task_id: which task
        - payload_dict: specific call parameters

        On-chain and off-chain can reconcile using this hash
        """
        canonical_payload = json.dumps(payload_dict, sort_keys=True, separators=(',', ':'))
        hash_input = f"{service_id}|{agent_id}|{task_id}|{canonical_payload}"
        return hashlib.sha256(hash_input.encode()).hexdigest()

    def pay_for_service(
        self,
        service_id: str,
        agent_id: str,
        task_id: str,
        quantity: int,
        payload_dict: Dict[str, Any],
        override_price: Optional[float] = None
    ) -> PaymentResult:
        """
        Complete payment flow (refactored version)

        Flow:
        1. Compute service_call_hash
        2. Get service pricing from config (for policy check only)
        3. Call PolicyEngine for budget and risk check
        4. Call Guardian /quote (pre-check)
        5. Call Guardian /pay (actual payment)
        6. Record usage
        """

        # Step 1: Compute serviceCallHash
        service_call_hash = self.build_service_call_hash(service_id, agent_id, task_id, payload_dict)
        print(f"[PAYMENT_CLIENT] ServiceCallHash: {service_call_hash}")

        # Step 2: Get service pricing (for policy check)
        service = None
        estimated_cost = 0.0

        if self.policy_engine:
            service = self.policy_engine.services.get(service_id)
            if service:
                if override_price is not None:
                    estimated_cost = override_price * quantity
                else:
                    estimated_cost = service.unitPrice * quantity

        # Step 3: Policy check (budget, risk, permissions)
        if self.policy_engine:
            print(f"[PAYMENT_CLIENT] Running policy check...")
            decision = self.policy_engine.evaluate(
                agent_id=agent_id,
                service_id=service_id,
                estimated_cost=estimated_cost,
                quantity=quantity,
                task_id=task_id,
                payload=payload_dict
            )

            print(f"[PAYMENT_CLIENT] Policy decision: {decision.action} - {decision.reason}")

            if decision.action == "DENY":
                return PaymentResult(
                    success=False,
                    error=f"Policy denied: {decision.reason}",
                    risk_level=decision.risk_level,
                    policy_action="DENY",
                    service_call_hash=service_call_hash
                )

            if decision.action == "DOWNGRADE":
                print(f"[PAYMENT_CLIENT] Downgrading quantity: {quantity} -> {decision.approved_quantity}")
                quantity = decision.approved_quantity
                # Recalculate cost
                if override_price is not None:
                    estimated_cost = override_price * quantity
                elif service:
                    estimated_cost = service.unitPrice * quantity

        # Step 4: Guardian Quote (pre-check Treasury balance etc)
        try:
            print(f"[PAYMENT_CLIENT] Calling Guardian /quote...")
            with httpx.Client(timeout=30.0) as client:
                quote_response = client.post(
                    f"{GUARDIAN_URL}/guardian/quote",
                    json={
                        "agent_id": agent_id,
                        "service_id": service_id,
                        "quantity": quantity,
                        "estimated_unit_price": estimated_cost / quantity if quantity > 0 else 0.0
                    }
                )

            if quote_response.status_code != 200:
                return PaymentResult(
                    success=False,
                    error=f"Guardian quote failed: HTTP {quote_response.status_code}",
                    service_call_hash=service_call_hash
                )

            quote_data = quote_response.json()
            if not quote_data.get("can_pay"):
                return PaymentResult(
                    success=False,
                    error=f"Guardian rejected: {quote_data.get('reason')}",
                    service_call_hash=service_call_hash
                )

            print(f"[PAYMENT_CLIENT] Guardian quote approved: {quote_data.get('reason')}")

        except Exception as e:
            print(f"[PAYMENT_CLIENT] Guardian quote failed: {e}")
            return PaymentResult(
                success=False,
                error=f"Guardian communication error: {str(e)}",
                service_call_hash=service_call_hash
            )

        # Step 5: Guardian Pay (actual payment)
        try:
            print(f"[PAYMENT_CLIENT] Calling Guardian /pay...")
            print(f"  Service: {service_id}")
            print(f"  Quantity: {quantity}")
            print(f"  Est. Cost: {estimated_cost} MNEE")

            with httpx.Client(timeout=60.0) as client:
                pay_response = client.post(
                    f"{GUARDIAN_URL}/guardian/pay",
                    json={
                        "agent_id": agent_id,
                        "service_id": service_id,
                        "task_id": task_id,
                        "quantity": quantity,
                        "service_call_hash": service_call_hash
                    }
                )

            if pay_response.status_code != 200:
                return PaymentResult(
                    success=False,
                    error=f"Guardian payment failed: HTTP {pay_response.status_code}",
                    service_call_hash=service_call_hash
                )

            pay_data = pay_response.json()
            if not pay_data.get("success"):
                return PaymentResult(
                    success=False,
                    error=f"Payment failed: {pay_data.get('reason')}",
                    service_call_hash=service_call_hash
                )

            payment_id = pay_data.get("payment_id", "")
            tx_hash = pay_data.get("tx_hash", "")

            print(f"[PAYMENT_CLIENT] Payment successful!")
            print(f"  PaymentID: {payment_id}")
            print(f"  TxHash: {tx_hash}")

            result = PaymentResult(
                success=True,
                payment_id=payment_id,
                tx_hash=tx_hash,
                service_call_hash=service_call_hash,
                amount=estimated_cost,
                risk_level="RISK_OK",
                policy_action="ALLOW"
            )

            # Step 6: Record usage
            self.record_usage(agent_id, service_id, estimated_cost, task_id, result)

            return result

        except Exception as e:
            print(f"[PAYMENT_CLIENT] Payment execution failed: {e}")
            return PaymentResult(
                success=False,
                error=str(e),
                service_call_hash=service_call_hash
            )

    def record_usage(self, agent_id: str, service_id: str, amount: float, task_id: str, payment_result: PaymentResult):
        """
        Record usage information

        Used for:
        - Auditing
        - Statistics
        - Updating Agent daily spending
        """
        today = date.today().isoformat()

        record = {
            "timestamp": datetime.now().isoformat(),
            "agent_id": agent_id,
            "service_id": service_id,
            "task_id": task_id,
            "amount": amount,
            "payment_id": payment_result.payment_id,
            "tx_hash": payment_result.tx_hash,
            "service_call_hash": payment_result.service_call_hash
        }

        self.usage_records.append(record)
        key = (agent_id, today)
        self.daily_spending[key] = self.daily_spending.get(key, 0.0) + amount

        # Update Agent spending in PolicyEngine
        if self.policy_engine:
            agent = self.policy_engine.agents.get(agent_id)
            if agent:
                agent.currentDailySpend += amount
                print(f"[PAYMENT_CLIENT] Updated {agent_id} daily spend: {agent.currentDailySpend:.2f} / {agent.dailyBudget:.2f} MNEE")

    def get_treasury_balance(self) -> float:
        """
        Query Treasury balance

        Now queries through Guardian (without direct access to private key)
        """
        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(f"{GUARDIAN_URL}/guardian/balance")

            if response.status_code == 200:
                data = response.json()
                return data.get("balance_mnee", 0.0)
            else:
                print(f"[PAYMENT_CLIENT] Failed to get balance: HTTP {response.status_code}")
                return 0.0

        except Exception as e:
            print(f"[PAYMENT_CLIENT] Failed to get balance: {e}")
            return 0.0
