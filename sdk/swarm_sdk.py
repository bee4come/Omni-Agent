"""
Swarm SDK - Multi-Agent Orchestration Interface

For developers who want to use the full Swarm architecture
with Manager, Customer, Merchant, and Treasurer agents.
"""

import sys
import os
from typing import Dict, Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from agents.swarm import SwarmOrchestrator
from payment.client import PaymentClient
from policy.engine import PolicyEngine


class SwarmSDK:
    """
    Multi-agent orchestration interface

    Example:
        swarm = SwarmSDK()
        result = swarm.execute("Generate an image and check ETH price")
        print(f"Cost: {result['total_cost']} MNEE")
    """

    def __init__(
        self,
        config_path: Optional[str] = None,
        services_path: Optional[str] = None
    ):
        """
        Initialize Swarm SDK

        Args:
            config_path: Path to agents.yaml
            services_path: Path to services.yaml
        """
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

        # Initialize Swarm
        self.orchestrator = SwarmOrchestrator(
            payment_client=self.payment_client,
            policy_engine=self.policy_engine
        )

        print("[SWARM_SDK] Initialized multi-agent orchestrator")

    def execute(
        self,
        user_request: str,
        agent_id: str = "swarm-user"
    ) -> Dict:
        """
        Execute a request through the Swarm

        This coordinates all agents:
        - Manager plans the tasks
        - Customer executes purchases
        - Merchant delivers services
        - Treasurer records transactions

        Args:
            user_request: Natural language request
            agent_id: Requesting agent ID

        Returns:
            Execution result with all details

        Example:
            result = swarm.execute("Generate 3 images")
            for task in result["tasks"]:
                if task["success"]:
                    print(f"Service: {task['service_id']}")
                    print(f"Data: {task['data']}")
        """
        swarm_result = self.orchestrator.process_request(
            user_request=user_request,
            requesting_agent_id=agent_id
        )

        # Simplify result structure
        return {
            "success": swarm_result["success"],
            "plan_id": swarm_result["plan_id"],
            "total_tasks": swarm_result["execution_summary"]["total_tasks"],
            "successful_tasks": swarm_result["execution_summary"]["successful_tasks"],
            "failed_tasks": swarm_result["execution_summary"]["failed_tasks"],
            "total_cost": swarm_result["financial_summary"]["total_spent"],
            "tasks": [
                {
                    "task_id": task["task_id"],
                    "service_id": task["service_id"],
                    "success": task["success"],
                    "payment_id": task.get("payment_id"),
                    "data": task.get("service_data"),
                    "error": task.get("error")
                }
                for task in swarm_result["task_results"]
            ]
        }

    def get_statistics(self) -> Dict:
        """
        Get system statistics from all agents

        Returns:
            Statistics from Manager, Customer, Merchant, Treasurer
        """
        return self.orchestrator.get_system_stats()

    def get_agent_report(self, agent_id: str) -> Dict:
        """
        Get detailed report for specific agent

        Args:
            agent_id: Agent to report on

        Returns:
            Agent-specific financial report
        """
        return self.orchestrator.get_agent_report(agent_id)

    def get_service_report(self, service_id: str) -> Dict:
        """
        Get detailed report for specific service

        Args:
            service_id: Service to report on

        Returns:
            Service-specific revenue report
        """
        return self.orchestrator.get_service_report(service_id)

    def detect_anomalies(self) -> Dict:
        """
        Detect financial anomalies

        Returns:
            Anomaly detection results
        """
        return self.orchestrator.detect_anomalies()

    def get_daily_summary(self) -> Dict:
        """
        Get daily financial summary

        Returns:
            Summary of today's transactions
        """
        stats = self.orchestrator.get_system_stats()
        return {
            "total_transactions": stats["treasurer"]["total_transactions"],
            "total_volume": stats["treasurer"]["total_volume"],
            "success_rate": stats["treasurer"]["success_rate"],
            "unique_agents": stats["treasurer"]["unique_agents"],
            "unique_services": stats["treasurer"]["unique_services"],
            "anomalies": stats["treasurer"]["anomalies_detected"]
        }
