"""
Manager Agent - Task Planning and Decomposition

Responsibilities:
- Analyze user requests
- Break down complex requests into atomic tasks
- Select appropriate services and merchants
- Create execution plans for Customer Agent
"""

import uuid
from typing import Dict, List, Optional
from pydantic import BaseModel
from datetime import datetime


class TaskPlan(BaseModel):
    """Structured plan for a single task"""
    task_id: str
    task_type: str  # "buy_service", "query_info", "compute"
    service_id: str
    merchant_id: Optional[str] = None
    payload: Dict
    quantity: int = 1
    priority: str = "MEDIUM"  # HIGH, MEDIUM, LOW
    estimated_cost: float = 0.0


class ExecutionPlan(BaseModel):
    """Complete execution plan for user request"""
    plan_id: str
    user_request: str
    agent_id: str
    tasks: List[TaskPlan]
    total_estimated_cost: float
    created_at: str


class ManagerAgent:
    """
    Manager Agent - Plans and decomposes user requests

    The Manager analyzes natural language requests and creates
    structured execution plans that Customer Agent can execute.
    """

    def __init__(self, agent_id: str = "manager-agent"):
        self.agent_id = agent_id
        self.plans_created = []

    def plan(self, user_request: str, requesting_agent_id: str = "user-agent") -> ExecutionPlan:
        """
        Analyze user request and create execution plan

        In a real implementation, this would use LLM to understand
        the request. For MVP, we use pattern matching.

        Args:
            user_request: Natural language user request
            requesting_agent_id: ID of agent making request

        Returns:
            ExecutionPlan with structured tasks
        """
        plan_id = f"plan-{uuid.uuid4().hex[:8]}"
        tasks = []
        total_cost = 0.0

        # Pattern matching for MVP (replace with LLM in production)
        request_lower = user_request.lower()

        # Pattern 1: Image generation
        if any(word in request_lower for word in ["image", "picture", "avatar", "generate", "draw"]):
            task = TaskPlan(
                task_id=f"task-{uuid.uuid4().hex[:6]}",
                task_type="buy_service",
                service_id="IMAGE_GEN_PREMIUM",
                merchant_id="merchant-1",
                payload={"prompt": user_request, "style": "cyberpunk"},
                quantity=1,
                priority="HIGH",
                estimated_cost=1.0
            )
            tasks.append(task)
            total_cost += task.estimated_cost

        # Pattern 2: Price query
        if any(word in request_lower for word in ["price", "cost", "how much", "eth", "mnee"]):
            task = TaskPlan(
                task_id=f"task-{uuid.uuid4().hex[:6]}",
                task_type="buy_service",
                service_id="PRICE_ORACLE",
                merchant_id="merchant-2",
                payload={"base": "ETH", "quote": "MNEE"},
                quantity=1,
                priority="MEDIUM",
                estimated_cost=0.05
            )
            tasks.append(task)
            total_cost += task.estimated_cost

        # Pattern 3: Batch computation
        if any(word in request_lower for word in ["compute", "calculate", "batch", "process"]):
            # Extract quantity if mentioned
            quantity = 1
            if "100" in request_lower:
                quantity = 100
            elif "50" in request_lower:
                quantity = 50
            elif "10" in request_lower:
                quantity = 10

            task = TaskPlan(
                task_id=f"task-{uuid.uuid4().hex[:6]}",
                task_type="buy_service",
                service_id="BATCH_COMPUTE",
                merchant_id="merchant-3",
                payload={"jobSize": quantity, "taskType": "synthetic"},
                quantity=1,
                priority="LOW",
                estimated_cost=3.0
            )
            tasks.append(task)
            total_cost += task.estimated_cost

        # Pattern 4: Log archival
        if any(word in request_lower for word in ["log", "archive", "store", "save"]):
            task = TaskPlan(
                task_id=f"task-{uuid.uuid4().hex[:6]}",
                task_type="buy_service",
                service_id="LOG_ARCHIVE",
                merchant_id="merchant-4",
                payload={"logData": user_request, "retention": "30days"},
                quantity=1,
                priority="LOW",
                estimated_cost=0.01
            )
            tasks.append(task)
            total_cost += task.estimated_cost

        # Fallback: If no patterns matched, create generic query task
        if not tasks:
            task = TaskPlan(
                task_id=f"task-{uuid.uuid4().hex[:6]}",
                task_type="query_info",
                service_id="GENERAL_QUERY",
                payload={"query": user_request},
                quantity=1,
                priority="HIGH",
                estimated_cost=0.0
            )
            tasks.append(task)

        plan = ExecutionPlan(
            plan_id=plan_id,
            user_request=user_request,
            agent_id=requesting_agent_id,
            tasks=tasks,
            total_estimated_cost=total_cost,
            created_at=datetime.now().isoformat()
        )

        self.plans_created.append(plan)
        print(f"[MANAGER] Created plan {plan_id} with {len(tasks)} tasks, est. cost: {total_cost} MNEE")

        return plan

    def get_plan_stats(self) -> Dict:
        """Get statistics about plans created"""
        return {
            "total_plans": len(self.plans_created),
            "total_tasks": sum(len(p.tasks) for p in self.plans_created),
            "total_estimated_cost": sum(p.total_estimated_cost for p in self.plans_created)
        }
