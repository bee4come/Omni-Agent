"""
Payment SDK - Simplified Payment Interface

For developers who want direct payment control without
the full Swarm architecture.
"""

import sys
import os
from typing import Dict, Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from payment.client import PaymentClient, PaymentResult
from policy.engine import PolicyEngine


class PaymentSDK:
    """
    Simplified payment interface

    Example:
        sdk = PaymentSDK(agent_id="my-agent")
        result = sdk.pay_for_service(
            service_id="IMAGE_GEN_PREMIUM",
            quantity=1,
            payload={"prompt": "cyberpunk"}
        )
    """

    def __init__(
        self,
        agent_id: str,
        config_path: Optional[str] = None,
        services_path: Optional[str] = None
    ):
        """
        Initialize Payment SDK

        Args:
            agent_id: Agent identifier
            config_path: Path to agents.yaml
            services_path: Path to services.yaml
        """
        self.agent_id = agent_id

        # Set default paths
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(__file__), '..', 'config', 'agents.yaml'
            )
        if services_path is None:
            services_path = os.path.join(
                os.path.dirname(__file__), '..', 'config', 'services.yaml'
            )

        # Initialize components
        self.policy_engine = PolicyEngine(config_path, services_path)
        self.payment_client = PaymentClient(policy_engine=self.policy_engine)

        print(f"[PAYMENT_SDK] Initialized for agent: {agent_id}")

    def pay_for_service(
        self,
        service_id: str,
        quantity: int = 1,
        payload: Dict = None,
        task_id: Optional[str] = None
    ) -> PaymentResult:
        """
        Pay for a service

        Args:
            service_id: Service identifier (e.g., "IMAGE_GEN_PREMIUM")
            quantity: Number of units to purchase
            payload: Service-specific parameters
            task_id: Optional task identifier (auto-generated if not provided)

        Returns:
            PaymentResult with payment details

        Example:
            result = sdk.pay_for_service(
                service_id="IMAGE_GEN_PREMIUM",
                payload={"prompt": "cyberpunk avatar"}
            )
            if result.success:
                print(f"Payment ID: {result.payment_id}")
                print(f"Cost: {result.amount} MNEE")
        """
        import uuid
        if task_id is None:
            task_id = f"task-{uuid.uuid4().hex[:8]}"

        if payload is None:
            payload = {}

        return self.payment_client.pay_for_service(
            service_id=service_id,
            agent_id=self.agent_id,
            task_id=task_id,
            quantity=quantity,
            payload_dict=payload
        )

    def check_policy(
        self,
        service_id: str,
        estimated_cost: float
    ) -> Dict:
        """
        Check if payment would be allowed by policy

        Args:
            service_id: Service identifier
            estimated_cost: Estimated cost in MNEE

        Returns:
            Policy decision

        Example:
            decision = sdk.check_policy("IMAGE_GEN_PREMIUM", 1.0)
            if decision["action"] == "ALLOW":
                # Proceed with payment
                pass
        """
        decision = self.policy_engine.evaluate(
            agent_id=self.agent_id,
            service_id=service_id,
            estimated_cost=estimated_cost,
            quantity=1,
            task_id="policy-check",
            payload={}
        )

        return {
            "action": decision.action,
            "approved_quantity": decision.approved_quantity,
            "risk_level": decision.risk_level,
            "reason": decision.reason
        }

    def get_service_price(self, service_id: str) -> Optional[float]:
        """
        Get price for a service

        Args:
            service_id: Service identifier

        Returns:
            Unit price in MNEE, or None if service not found
        """
        service = self.policy_engine.services.get(service_id)
        return service.unitPrice if service else None

    def get_treasury_balance(self) -> float:
        """Get current treasury balance"""
        return self.payment_client.get_treasury_balance()

    def get_agent_budget(self) -> Dict:
        """Get agent's budget information"""
        agent = self.policy_engine.agents.get(self.agent_id)
        if not agent:
            return {"error": f"Agent {self.agent_id} not found"}

        return {
            "daily_budget": agent.dailyBudget,
            "current_spending": agent.currentDailySpend,
            "remaining": agent.dailyBudget - agent.currentDailySpend,
            "max_per_call": agent.maxPerCall,
            "priority": agent.priority
        }
