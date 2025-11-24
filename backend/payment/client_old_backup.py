import os
import json
import hashlib
from typing import Dict, Any, Optional
from pydantic import BaseModel
from dotenv import load_dotenv
from datetime import datetime, date
from payment.mnee_sdk import Mnee

load_dotenv()

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
    def __init__(self, policy_engine=None):
        # Initialize MNEE SDK (Web3)
        self.mnee = Mnee({
            "environment": os.getenv("MNEE_ENV", "local")
        })
        
        self.policy_engine = policy_engine
        
        # Usage tracking
        self.usage_records = []
        self.daily_spending = {} 
        
        self.treasury_key = os.getenv("TREASURY_PRIVATE_KEY", "")
        if not self.treasury_key:
             print("WARNING: TREASURY_PRIVATE_KEY not set. Payments will fail.")

    def build_service_call_hash(self, service_id: str, agent_id: str, task_id: str, payload_dict: Dict[str, Any]) -> str:
        """
        Compute a deterministic hash representing the service invocation payload.
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
        Complete payment flow using MNEE Payment Router.
        """
        # Step 1: Compute serviceCallHash
        service_call_hash = self.build_service_call_hash(service_id, agent_id, task_id, payload_dict)
        
        # Step 2: Get service details and cost (For Policy Check only)
        # The actual cost is determined on-chain by the Registry
        service = None
        estimated_cost = 0.0
        
        if self.policy_engine:
            service = self.policy_engine.services.get(service_id)
            if service:
                if override_price is not None:
                    estimated_cost = override_price * quantity
                else:
                    estimated_cost = service.unitPrice * quantity
        
        # Step 3: Policy + Risk check
        if self.policy_engine:
            decision = self.policy_engine.evaluate(
                agent_id=agent_id,
                service_id=service_id,
                estimated_cost=estimated_cost,
                quantity=quantity,
                task_id=task_id,
                payload=payload_dict
            )
            
            if decision.action == "DENY":
                return PaymentResult(
                    success=False,
                    error=decision.reason,
                    risk_level=decision.risk_level,
                    policy_action="DENY"
                )
            
            if decision.action == "DOWNGRADE":
                quantity = decision.approved_quantity
                # Recalculate cost for record keeping
                if override_price is not None:
                    estimated_cost = override_price * quantity
                elif service:
                    estimated_cost = service.unitPrice * quantity
        
        # Step 4: Execute MNEE Payment Router Transaction
        try:
            print(f"[PAYMENT_CLIENT] Initiating Payment via Router...")
            print(f"  Service: {service_id}")
            print(f"  Cost (Est): {estimated_cost} MNEE")
            
            # Ensure Approval (Idempotent)
            # We assume estimated_cost is correct enough for approval, 
            # or we approve max once.
            # Using a large amount for approval to avoid repeated txs
            if self.treasury_key:
                 self.mnee.ensure_approval(self.treasury_key)

            # Call SDK Router Pay
            response = self.mnee.pay_for_service(
                service_id=service_id,
                agent_id=agent_id,
                task_id=task_id,
                quantity=quantity,
                service_call_hash=service_call_hash,
                private_key=self.treasury_key
            )
            
            ticket_id = response.ticketId
            print(f"[PAYMENT_CLIENT] Payment Successful! ID: {ticket_id}")
            
            result = PaymentResult(
                success=True,
                payment_id=ticket_id,
                tx_hash=response.rawtx,
                service_call_hash=service_call_hash,
                amount=estimated_cost,
                risk_level="RISK_OK",
                policy_action="ALLOW"
            )
            
            # Step 5: Record usage
            self.record_usage(agent_id, service_id, estimated_cost, task_id, result)
            
            return result
            
        except Exception as e:
            print(f"[PAYMENT_CLIENT] Payment failed: {e}")
            return PaymentResult(
                success=False,
                error=str(e),
                service_call_hash=service_call_hash
            )
    
    def record_usage(self, agent_id: str, service_id: str, amount: float, task_id: str, payment_result: PaymentResult):
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
        
        if self.policy_engine:
            agent = self.policy_engine.agents.get(agent_id)
            if agent:
                agent.currentDailySpend += amount
    
    def get_treasury_balance(self) -> float:
        try:
            # We need the address associated with the key
            # But client doesn't store address directly. 
            # We can derive it or just ask SDK to balance(address) if we knew it.
            # For now, let's assume we can get it from the key in SDK or configured.
            # The SDK's balance method takes an address.
            from eth_account import Account
            if self.treasury_key:
                address = Account.from_key(self.treasury_key).address
                balance_info = self.mnee.balance(address)
                return balance_info['decimalAmount']
            return 0.0
        except Exception as e:
            print(f"[PAYMENT_CLIENT] Failed to get balance: {e}")
            return 0.0