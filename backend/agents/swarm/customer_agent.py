"""
Customer Agent - Purchase Execution

Responsibilities:
- Execute tasks from Manager's plan
- Request quotes from Merchant Agents
- Initiate payments via Payment Client
- Retrieve delivered services
- Handle errors and retries
"""

import uuid
from typing import Dict, Optional
from pydantic import BaseModel
from datetime import datetime


class PurchaseResult(BaseModel):
    """Result of a purchase attempt"""
    success: bool
    task_id: str
    service_id: str
    payment_id: Optional[str] = None
    service_result: Optional[Dict] = None
    error: Optional[str] = None
    cost: float = 0.0


class CustomerAgent:
    """
    Customer Agent - Executes purchases on behalf of user

    The Customer Agent coordinates the full purchase flow:
    1. Request quote from Merchant
    2. Check with Policy Engine
    3. Execute payment via Payment Client
    4. Retrieve delivered service
    """

    def __init__(self, agent_id: str = "customer-agent", payment_client=None, policy_engine=None):
        self.agent_id = agent_id
        self.payment_client = payment_client
        self.policy_engine = policy_engine
        self.purchase_history = []

    def execute_task(self, task_plan, merchant_agent=None) -> PurchaseResult:
        """
        Execute a single task from Manager's plan

        Args:
            task_plan: TaskPlan object from Manager
            merchant_agent: MerchantAgent instance (optional, for direct calls)

        Returns:
            PurchaseResult with outcome
        """
        print(f"[CUSTOMER] Executing task {task_plan.task_id}: {task_plan.service_id}")

        try:
            # Step 1: Request quote from Merchant
            if merchant_agent:
                quote = merchant_agent.quote(task_plan.service_id, task_plan.payload)
                print(f"[CUSTOMER] Received quote: {quote['unit_price_mnee']} MNEE")
            else:
                # Fallback: use estimated cost from plan
                quote = {
                    "unit_price_mnee": task_plan.estimated_cost,
                    "merchant_id": task_plan.merchant_id or "unknown",
                    "estimated_latency": "unknown"
                }

            # Step 2: Execute payment via Payment Client
            if self.payment_client and task_plan.estimated_cost > 0:
                payment_result = self.payment_client.pay_for_service(
                    service_id=task_plan.service_id,
                    agent_id=self.agent_id,
                    task_id=task_plan.task_id,
                    quantity=task_plan.quantity,
                    payload_dict=task_plan.payload,
                    override_price=quote["unit_price_mnee"]
                )

                if not payment_result.success:
                    return PurchaseResult(
                        success=False,
                        task_id=task_plan.task_id,
                        service_id=task_plan.service_id,
                        error=f"Payment failed: {payment_result.error}",
                        cost=0.0
                    )

                payment_id = payment_result.payment_id
                service_call_hash = payment_result.service_call_hash
                actual_cost = payment_result.amount

                print(f"[CUSTOMER] Payment successful: {payment_id}")

                # Step 3: Request service delivery from Merchant
                if merchant_agent:
                    service_result = merchant_agent.fulfill(
                        service_id=task_plan.service_id,
                        task_id=task_plan.task_id,
                        payment_id=payment_id,
                        service_call_hash=service_call_hash,
                        payload=task_plan.payload
                    )
                else:
                    # Mock result if no merchant available
                    service_result = {
                        "status": "delivered",
                        "data": {"result": "mock_service_output"}
                    }

                print(f"[CUSTOMER] Service delivered for task {task_plan.task_id}")

                result = PurchaseResult(
                    success=True,
                    task_id=task_plan.task_id,
                    service_id=task_plan.service_id,
                    payment_id=payment_id,
                    service_result=service_result,
                    cost=actual_cost
                )

            else:
                # No payment needed (free service or mock mode)
                result = PurchaseResult(
                    success=True,
                    task_id=task_plan.task_id,
                    service_id=task_plan.service_id,
                    service_result={"status": "completed", "data": {"query_result": "mock_response"}},
                    cost=0.0
                )

            self.purchase_history.append(result)
            return result

        except Exception as e:
            print(f"[CUSTOMER] Task execution failed: {e}")
            error_result = PurchaseResult(
                success=False,
                task_id=task_plan.task_id,
                service_id=task_plan.service_id,
                error=str(e),
                cost=0.0
            )
            self.purchase_history.append(error_result)
            return error_result

    def execute_plan(self, execution_plan, merchant_agent=None) -> Dict:
        """
        Execute all tasks in a plan sequentially

        Args:
            execution_plan: ExecutionPlan from Manager
            merchant_agent: MerchantAgent instance (optional)

        Returns:
            Summary of execution results
        """
        print(f"[CUSTOMER] Executing plan {execution_plan.plan_id} with {len(execution_plan.tasks)} tasks")

        results = []
        total_cost = 0.0
        success_count = 0

        for task in execution_plan.tasks:
            result = self.execute_task(task, merchant_agent)
            results.append(result)
            total_cost += result.cost
            if result.success:
                success_count += 1

        summary = {
            "plan_id": execution_plan.plan_id,
            "total_tasks": len(execution_plan.tasks),
            "successful_tasks": success_count,
            "failed_tasks": len(execution_plan.tasks) - success_count,
            "total_cost": total_cost,
            "results": results
        }

        print(f"[CUSTOMER] Plan execution complete: {success_count}/{len(execution_plan.tasks)} succeeded, cost: {total_cost} MNEE")

        return summary

    def get_purchase_stats(self) -> Dict:
        """Get statistics about purchases made"""
        successful = [p for p in self.purchase_history if p.success]
        failed = [p for p in self.purchase_history if not p.success]

        return {
            "total_purchases": len(self.purchase_history),
            "successful": len(successful),
            "failed": len(failed),
            "total_spent": sum(p.cost for p in successful),
            "services_used": list(set(p.service_id for p in successful))
        }
