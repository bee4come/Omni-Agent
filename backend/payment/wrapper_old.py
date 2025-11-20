from typing import Any, Callable, Optional
from policy.engine import PolicyEngine
from payment.client import PaymentClient
from policy.logger import SystemLogger
import uuid

class PaidToolWrapper:
    def __init__(self, policy_engine: PolicyEngine, payment_client: PaymentClient, logger: Optional[SystemLogger] = None):
        self.policy = policy_engine
        self.payment = payment_client
        self.logger = logger or SystemLogger()

    def wrap(self, tool_func: Callable, service_id: str, agent_id: str, cost_per_call: float = 1.0):
        """
        Decorator-like wrapper that enforces policy and payment before execution.
        """
        def wrapper(*args, **kwargs):
            # 1. Check Policy
            decision = self.policy.check_policy(agent_id, service_id)
            
            if not decision.allowed:
                print(f"[POLICY BLOCKED] Agent={agent_id} Service={service_id} Reason={decision.reason}")
                self.logger.log_policy_decision(agent_id, service_id, "REJECTED", decision.reason, cost_per_call)
                return {"error": "Policy Rejected", "reason": decision.reason}

            # 2. Handle Downgrade (if applicable)
            effective_service_id = service_id
            if decision.new_service_id:
                print(f"[POLICY DOWNGRADE] Switching {service_id} -> {decision.new_service_id}")
                self.logger.log_policy_decision(agent_id, service_id, "DOWNGRADED", f"Switched to {decision.new_service_id}", cost_per_call)
                effective_service_id = decision.new_service_id
                # In a real app, we might swap the tool_func here too.
            else:
                self.logger.log_policy_decision(agent_id, service_id, "ALLOWED", decision.reason, cost_per_call)

            # 3. Execute Payment (On-chain)
            task_id = str(uuid.uuid4())
            tx_hash = "0xMOCK_TX_HASH"
            try:
                tx_hash = self.payment.pay_for_service(effective_service_id, agent_id, task_id)
                self.policy.record_spend(agent_id, cost_per_call) # Update local budget tracking
                self.logger.log_transaction(agent_id, effective_service_id, task_id, cost_per_call, tx_hash, "SUCCESS")
            except Exception as e:
                print(f"Payment failed: {e}")
                self.logger.log_transaction(agent_id, effective_service_id, task_id, cost_per_call, None, "FAILED")
                # Depending on strictness, we might return error or proceed if it's a demo
                # return {"error": "Payment Failed"}

            # 4. Execute Tool
            print(f"Executing tool {effective_service_id} for {agent_id}...")
            result = tool_func(*args, **kwargs)
            
            # Attach metadata
            if isinstance(result, dict):
                result['_payment_tx'] = tx_hash
                result['_policy_decision'] = decision.reason
                result['_task_id'] = task_id
            
            return result
        
        return wrapper
