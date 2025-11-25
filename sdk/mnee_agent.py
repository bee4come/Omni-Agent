"""
MNEE Agent - High-level Agent Interface

Provides a simple, unified interface for AI agents to use
MNEE-based services with automatic payment handling.
"""

import sys
import os
from typing import Dict, Optional, List

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from payment.client import PaymentClient
from policy.engine import PolicyEngine
from agents.swarm import SwarmOrchestrator


class MNEEAgent:
    """
    High-level agent interface for MNEE-based services

    Example:
        agent = MNEEAgent(agent_id="my-agent")
        result = agent.request_service("Generate a cyberpunk image")
    """

    def __init__(
        self,
        agent_id: str,
        config_path: Optional[str] = None,
        services_path: Optional[str] = None,
        use_swarm: bool = True
    ):
        """
        Initialize MNEE Agent

        Args:
            agent_id: Unique agent identifier
            config_path: Path to agents.yaml (default: ../config/agents.yaml)
            services_path: Path to services.yaml (default: ../config/services.yaml)
            use_swarm: Use Swarm architecture for coordination (default: True)
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

        # Initialize Swarm if requested
        self.use_swarm = use_swarm
        if use_swarm:
            self.swarm = SwarmOrchestrator(
                payment_client=self.payment_client,
                policy_engine=self.policy_engine
            )
        else:
            self.swarm = None

        print(f"[MNEE_AGENT] Initialized agent: {agent_id}")
        print(f"[MNEE_AGENT] Swarm mode: {'enabled' if use_swarm else 'disabled'}")

    def request_service(self, user_request: str) -> Dict:
        """
        Request a service with natural language

        This is the main entry point for agents. The system will:
        1. Analyze the request (via Manager)
        2. Check budget and policy
        3. Execute payment (via Guardian)
        4. Deliver service
        5. Record transaction

        Args:
            user_request: Natural language service request

        Returns:
            Result dictionary with service output and payment info

        Example:
            result = agent.request_service("Generate an image")
            if result["success"]:
                print(result["service_data"])
        """
        if self.use_swarm:
            # Use Swarm orchestration
            swarm_result = self.swarm.process_request(
                user_request=user_request,
                requesting_agent_id=self.agent_id
            )

            # Extract relevant info for simple API
            return {
                "success": swarm_result["success"],
                "message": user_request,
                "plan_id": swarm_result["plan_id"],
                "tasks": swarm_result["task_results"],
                "total_cost": swarm_result["financial_summary"]["total_spent"],
                "service_data": [
                    task["service_data"]
                    for task in swarm_result["task_results"]
                    if task["success"] and task["service_data"]
                ]
            }
        else:
            # Direct payment (legacy mode)
            return {
                "success": False,
                "error": "Direct mode not implemented. Please use use_swarm=True"
            }

    def get_balance(self) -> float:
        """
        Get treasury balance

        Returns:
            Current MNEE balance
        """
        return self.payment_client.get_treasury_balance()

    def get_budget_status(self) -> Dict:
        """
        Get current budget status for this agent

        Returns:
            Budget information including daily limit and spending
        """
        agent_config = self.policy_engine.agents.get(self.agent_id)
        if not agent_config:
            return {"error": f"Agent {self.agent_id} not found in configuration"}

        return {
            "agent_id": self.agent_id,
            "daily_budget": agent_config.dailyBudget,
            "current_spending": agent_config.currentDailySpend,
            "remaining_budget": agent_config.dailyBudget - agent_config.currentDailySpend,
            "max_per_call": agent_config.maxPerCall,
            "priority": agent_config.priority
        }

    def list_available_services(self) -> List[Dict]:
        """
        List all available services

        Returns:
            List of service configurations
        """
        return [
            {
                "id": service_id,
                "unit_price": service.unitPrice,
                "active": service.active,
                "provider": service.providerAddress
            }
            for service_id, service in self.policy_engine.services.items()
        ]

    def get_transaction_history(self) -> List[Dict]:
        """
        Get transaction history for this agent

        Returns:
            List of transactions
        """
        return self.payment_client.usage_records

    def get_statistics(self) -> Dict:
        """
        Get comprehensive statistics

        Returns:
            Statistics including spending, services used, etc.
        """
        if self.use_swarm:
            return self.swarm.get_system_stats()
        else:
            return {
                "transactions": len(self.payment_client.usage_records),
                "total_spent": sum(
                    r["amount"] for r in self.payment_client.usage_records
                )
            }
