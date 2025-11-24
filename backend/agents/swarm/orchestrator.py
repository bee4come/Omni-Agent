"""
Swarm Orchestrator - Multi-Agent Coordination

Coordinates all agents in the Swarm to execute user requests:
1. Manager creates execution plan
2. Customer executes purchases
3. Merchant provides services
4. Treasurer records transactions

This implements the A2A (Agent-to-Agent) commerce flow.
"""

from typing import Dict, Optional
from .manager_agent import ManagerAgent
from .customer_agent import CustomerAgent
from .merchant_agent import MerchantAgent
from .treasurer_agent import TreasurerAgent


class SwarmOrchestrator:
    """
    Swarm Orchestrator - Coordinates multi-agent workflows

    This is the main entry point for executing user requests
    through the Swarm architecture.
    """

    def __init__(self, payment_client=None, policy_engine=None):
        """
        Initialize Swarm with all agents

        Args:
            payment_client: PaymentClient instance (calls Guardian)
            policy_engine: PolicyEngine instance
        """
        self.manager = ManagerAgent(agent_id="manager-agent")
        self.customer = CustomerAgent(
            agent_id="customer-agent",
            payment_client=payment_client,
            policy_engine=policy_engine
        )
        self.merchant = MerchantAgent(merchant_id="merchant-1")
        self.treasurer = TreasurerAgent(agent_id="treasurer-agent")

        print("[SWARM] Orchestrator initialized with all agents")

    def process_request(self, user_request: str, requesting_agent_id: str = "user-agent") -> Dict:
        """
        Process user request through complete Swarm workflow

        Flow:
        1. Manager analyzes request and creates plan
        2. Customer executes plan (purchases services)
        3. Merchant delivers services
        4. Treasurer records all transactions

        Args:
            user_request: Natural language user request
            requesting_agent_id: ID of requesting agent

        Returns:
            Complete execution result with all agent outputs
        """
        print(f"\n[SWARM] Processing request: '{user_request}'")
        print("=" * 70)

        # Step 1: Manager creates execution plan
        print("\n[SWARM] Step 1: Manager creating plan...")
        execution_plan = self.manager.plan(user_request, requesting_agent_id)

        print(f"[SWARM] Plan created: {len(execution_plan.tasks)} tasks, est. cost: {execution_plan.total_estimated_cost} MNEE")

        # Step 2: Customer executes plan
        print("\n[SWARM] Step 2: Customer executing plan...")
        execution_summary = self.customer.execute_plan(execution_plan, self.merchant)

        print(f"[SWARM] Execution complete: {execution_summary['successful_tasks']}/{execution_summary['total_tasks']} succeeded")

        # Step 3: Treasurer records all successful transactions
        print("\n[SWARM] Step 3: Treasurer recording transactions...")
        transaction_records = []

        for result in execution_summary["results"]:
            if result.success and result.payment_id:
                receipt = {
                    "agent_id": requesting_agent_id,
                    "service_id": result.service_id,
                    "task_id": result.task_id,
                    "payment_id": result.payment_id,
                    "amount": result.cost,
                    "status": "success",
                    "service_call_hash": result.service_result.get("service_call_hash", "") if result.service_result else "",
                    "policy_action": "ALLOW",
                    "risk_level": "RISK_OK"
                }
                record = self.treasurer.record_transaction(receipt)
                transaction_records.append(record)

        print(f"[SWARM] Recorded {len(transaction_records)} transactions")

        # Step 4: Compile complete result
        print("\n[SWARM] Step 4: Compiling results...")
        print("=" * 70)

        swarm_result = {
            "success": execution_summary["successful_tasks"] > 0,
            "user_request": user_request,
            "plan_id": execution_plan.plan_id,
            "execution_summary": {
                "total_tasks": execution_summary["total_tasks"],
                "successful_tasks": execution_summary["successful_tasks"],
                "failed_tasks": execution_summary["failed_tasks"],
                "total_cost": execution_summary["total_cost"]
            },
            "task_results": [
                {
                    "task_id": r.task_id,
                    "service_id": r.service_id,
                    "success": r.success,
                    "payment_id": r.payment_id,
                    "service_data": r.service_result.get("data") if r.service_result else None,
                    "error": r.error
                }
                for r in execution_summary["results"]
            ],
            "financial_summary": {
                "transactions_recorded": len(transaction_records),
                "total_spent": execution_summary["total_cost"],
                "estimated_cost": execution_plan.total_estimated_cost
            }
        }

        print(f"[SWARM] Request processing complete!")
        print(f"[SWARM] Success: {swarm_result['success']}")
        print(f"[SWARM] Cost: {swarm_result['financial_summary']['total_spent']} MNEE")

        return swarm_result

    def get_system_stats(self) -> Dict:
        """Get statistics from all agents"""
        return {
            "manager": self.manager.get_plan_stats(),
            "customer": self.customer.get_purchase_stats(),
            "merchant": self.merchant.get_merchant_stats(),
            "treasurer": self.treasurer.get_summary()
        }

    def get_agent_report(self, agent_id: str) -> Dict:
        """Get detailed report for specific agent"""
        return self.treasurer.get_agent_report(agent_id)

    def get_service_report(self, service_id: str) -> Dict:
        """Get detailed report for specific service"""
        return self.treasurer.get_service_report(service_id)

    def detect_anomalies(self) -> Dict:
        """Detect any financial anomalies"""
        anomalies = self.treasurer.detect_anomalies()
        return {
            "anomalies_detected": len(anomalies),
            "anomalies": anomalies
        }
