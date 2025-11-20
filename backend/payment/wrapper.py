from typing import Any, Callable, Optional, Dict
from policy.engine import PolicyEngine
from payment.client import PaymentClient, PaymentResult
from policy.logger import SystemLogger
import uuid

class PaidToolWrapper:
    """
    Enhanced tool wrapper with anti-spoofing support via serviceCallHash.
    """
    
    def __init__(self, policy_engine: PolicyEngine, payment_client: PaymentClient, logger: Optional[SystemLogger] = None):
        self.policy = policy_engine
        self.payment = payment_client
        self.logger = logger or SystemLogger()
        
        # Ensure payment client has reference to policy engine
        if self.payment.policy_engine is None:
            self.payment.policy_engine = self.policy
    
    def wrap(self, tool_func: Callable, service_id: str, agent_id: str, cost_per_call: float = 1.0):
        """
        Decorator-like wrapper that enforces policy, risk, and payment before execution.
        
        This version integrates serviceCallHash for anti-spoofing.
        """
        def wrapper(*args, payload_dict: Optional[Dict[str, Any]] = None, **kwargs):
            # Generate unique task ID
            task_id = str(uuid.uuid4())
            
            # Build payload dict if not provided
            if payload_dict is None:
                payload_dict = {
                    'args': args,
                    'kwargs': kwargs
                }
            
            # Get quantity (default to 1)
            quantity = kwargs.get('quantity', 1)
            
            # Step 1: Policy + Risk + Payment (all in one via PaymentClient)
            payment_result: PaymentResult = self.payment.pay_for_service(
                service_id=service_id,
                agent_id=agent_id,
                task_id=task_id,
                quantity=quantity,
                payload_dict=payload_dict
            )
            
            # Step 2: Handle payment result
            if not payment_result.success:
                print(f"[PAID_TOOL_WRAPPER] Payment denied: {payment_result.error}")
                self.logger.log_policy_decision(
                    agent_id=agent_id,
                    service_id=service_id,
                    action=payment_result.policy_action,
                    reason=payment_result.error,
                    cost=cost_per_call,
                    risk_level=payment_result.risk_level
                )
                
                # Record failed attempt for risk tracking
                self.policy.record_call_result(agent_id, service_id, cost_per_call, success=False)
                
                return {
                    "error": "Policy Rejected" if payment_result.policy_action == "DENY" else "Payment Failed",
                    "reason": payment_result.error,
                    "riskLevel": payment_result.risk_level,
                    "policyAction": payment_result.policy_action
                }
            
            # Log successful payment decision
            self.logger.log_policy_decision(
                agent_id=agent_id,
                service_id=service_id,
                action=payment_result.policy_action,
                reason="Approved",
                cost=payment_result.amount,
                risk_level=payment_result.risk_level
            )
            
            self.logger.log_transaction(
                agent_id=agent_id,
                service_id=service_id,
                task_id=task_id,
                amount=payment_result.amount,
                tx_hash=payment_result.tx_hash,
                status="PENDING",
                service_call_hash=payment_result.service_call_hash
            )
            
            # Step 3: Execute tool with anti-spoofing metadata
            print(f"[PAID_TOOL_WRAPPER] Executing tool {service_id} for {agent_id}...")
            print(f"[PAID_TOOL_WRAPPER] ServiceCallHash: {payment_result.service_call_hash}")
            
            try:
                # Pass serviceCallHash and taskId to provider
                tool_kwargs = {
                    **kwargs,
                    'task_id': task_id,
                    'service_call_hash': payment_result.service_call_hash
                }
                
                result = tool_func(*args, **tool_kwargs)
                
                # Record successful call
                self.policy.record_call_result(agent_id, service_id, payment_result.amount, success=True)
                
                # Update transaction status to SUCCESS
                self.logger.log_transaction(
                    agent_id=agent_id,
                    service_id=service_id,
                    task_id=task_id,
                    amount=payment_result.amount,
                    tx_hash=payment_result.tx_hash,
                    status="SUCCESS",
                    service_call_hash=payment_result.service_call_hash
                )
                
                # Attach payment metadata to result
                if isinstance(result, dict):
                    result['_payment_tx'] = payment_result.tx_hash
                    result['_payment_id'] = payment_result.payment_id
                    result['_service_call_hash'] = payment_result.service_call_hash
                    result['_task_id'] = task_id
                    result['_policy_decision'] = "Approved"
                    result['_risk_level'] = payment_result.risk_level
                    result['_amount'] = payment_result.amount
                
                return result
                
            except Exception as e:
                print(f"[PAID_TOOL_WRAPPER] Tool execution failed: {e}")
                
                # Record failure
                self.policy.record_call_result(agent_id, service_id, payment_result.amount, success=False)
                
                return {
                    "error": "Tool Execution Failed",
                    "reason": str(e),
                    "_payment_tx": payment_result.tx_hash,
                    "_service_call_hash": payment_result.service_call_hash,
                    "_task_id": task_id
                }
        
        return wrapper
    
    def execute_with_payment(
        self,
        tool_func: Callable,
        service_id: str,
        agent_id: str,
        payload_dict: Dict[str, Any],
        quantity: int = 1
    ) -> Dict[str, Any]:
        """
        Direct execution method (non-decorator style) with full anti-spoofing support.
        
        This is useful for LangGraph nodes where decorator pattern is inconvenient.
        """
        wrapped = self.wrap(tool_func, service_id, agent_id)
        return wrapped(payload_dict=payload_dict, quantity=quantity)
