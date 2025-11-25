"""
MNEE Nexus / Omni-Agent API - LangGraph Architecture

This is the refactored version using structured GraphState and nodes.
Main improvements:
- Structured state flow through GraphState
- Clear separation: Planner -> Guardian -> Executor -> Summarizer
- All payments go through single enforcement point
- Complete audit trail via StepRecord
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os
from dotenv import load_dotenv

load_dotenv()

from fastapi.middleware.cors import CORSMiddleware

# Import new graph architecture
from agents.graph import get_agent_graph
from agents.merchant_agent import router as merchant_router
from policy.engine import PolicyEngine
from policy.logger import SystemLogger
from pathlib import Path

app = FastAPI(
    title="MNEE Nexus / Omni-Agent API (Graph Architecture)",
    description="Programmable Payment Orchestrator for AI Agents - Structured Graph Edition",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(merchant_router)

# Initialize graph singleton
agent_graph = get_agent_graph()

# Also keep references to policy/logger for API endpoints
backend_dir = Path(__file__).parent.parent
project_root = backend_dir.parent
default_agents_path = project_root / "config" / "agents.yaml"
default_services_path = project_root / "config" / "services.yaml"

policy_engine = PolicyEngine(
    agents_path=os.getenv("POLICY_CONFIG_PATH", str(default_agents_path)),
    services_path=os.getenv("SERVICE_CONFIG_PATH", str(default_services_path))
)
logger = SystemLogger()


class ChatRequest(BaseModel):
    agent_id: str
    message: str
    task_id: Optional[str] = None


class BudgetUpdateRequest(BaseModel):
    daily_budget: Optional[float] = None
    max_per_call: Optional[float] = None


@app.get("/")
def root():
    return {
        "name": "MNEE Nexus / Omni-Agent (Graph Architecture)",
        "version": "2.0.0",
        "status": "running",
        "architecture": "LangGraph with structured state flow"
    }


@app.post("/chat")
def chat(request: ChatRequest):
    """
    Send a message to an agent and get a response.

    New graph architecture:
    - Planner converts message to structured plan
    - Guardian assesses each step for risk
    - Executor enforces payment before execution
    - Summarizer generates final response

    Returns structured result with full audit trail.
    """
    try:
        result = agent_graph.invoke(
            agent_id=request.agent_id,
            user_message=request.message,
            task_id=request.task_id
        )

        return {
            "response": result['final_answer'],
            "agent_id": result['agent_id'],
            "task_id": result['task_id'],
            "steps": result['steps'],
            "success": result['success']
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/treasury")
def get_treasury_status():
    """Get the overall treasury status including all agents' budgets and spending."""
    agents_data = {}
    for agent_id, agent in policy_engine.agents.items():
        agents_data[agent_id] = {
            "id": agent.id,
            "priority": agent.priority,
            "dailyBudget": agent.dailyBudget,
            "maxPerCall": agent.maxPerCall,
            "currentDailySpend": agent.currentDailySpend,
            "remainingBudget": agent.dailyBudget - agent.currentDailySpend
        }

    return {
        "agents": agents_data,
        "totalAllocated": sum(a.dailyBudget for a in policy_engine.agents.values()),
        "totalSpent": sum(a.currentDailySpend for a in policy_engine.agents.values())
    }


@app.get("/agents")
def get_all_agents():
    """Get list of all configured agents"""
    return {
        "agents": [
            {
                "id": agent.id,
                "priority": agent.priority,
                "dailyBudget": agent.dailyBudget,
                "maxPerCall": agent.maxPerCall,
                "currentDailySpend": agent.currentDailySpend
            }
            for agent in policy_engine.agents.values()
        ]
    }


@app.get("/agents/{agent_id}")
def get_agent(agent_id: str):
    """Get detailed info about a specific agent"""
    agent = policy_engine.agents.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")

    return {
        "id": agent.id,
        "priority": agent.priority,
        "dailyBudget": agent.dailyBudget,
        "maxPerCall": agent.maxPerCall,
        "currentDailySpend": agent.currentDailySpend,
        "remainingBudget": agent.dailyBudget - agent.currentDailySpend,
        "transactions": logger.get_agent_transactions(agent_id),
        "totalSpent": logger.get_total_spent_by_agent(agent_id)
    }


@app.put("/agents/{agent_id}/budget")
def update_agent_budget(agent_id: str, request: BudgetUpdateRequest):
    """Update an agent's budget configuration"""
    agent = policy_engine.agents.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")

    if request.daily_budget is not None:
        agent.dailyBudget = request.daily_budget
    if request.max_per_call is not None:
        agent.maxPerCall = request.max_per_call

    return {
        "message": "Budget updated successfully",
        "agent": {
            "id": agent.id,
            "dailyBudget": agent.dailyBudget,
            "maxPerCall": agent.maxPerCall
        }
    }


@app.get("/services")
def get_all_services():
    """Get list of all configured services"""
    return {
        "services": [
            {
                "id": service.id,
                "unitPrice": service.unitPrice,
                "providerAddress": service.providerAddress,
                "active": service.active,
                "isVerified": getattr(service, 'isVerified', False),
                "metadataURI": getattr(service, 'metadataURI', ''),
                "maxDailySpending": getattr(service, 'maxDailySpending', None),
                "allowedAgents": getattr(service, 'allowedAgents', None),
                "blockedAgents": getattr(service, 'blockedAgents', None)
            }
            for service in policy_engine.services.values()
        ]
    }


@app.get("/services/{service_id}")
def get_service(service_id: str):
    """Get detailed info about a specific service"""
    service = policy_engine.services.get(service_id)
    if not service:
        raise HTTPException(status_code=404, detail=f"Service {service_id} not found")

    return {
        "id": service.id,
        "unitPrice": service.unitPrice,
        "providerAddress": service.providerAddress,
        "active": service.active,
        "isVerified": getattr(service, 'isVerified', False),
        "metadataURI": getattr(service, 'metadataURI', ''),
        "maxDailySpending": getattr(service, 'maxDailySpending', None),
        "allowedAgents": getattr(service, 'allowedAgents', None),
        "blockedAgents": getattr(service, 'blockedAgents', None),
        "transactions": logger.get_service_transactions(service_id),
        "totalRevenue": logger.get_total_revenue_by_service(service_id)
    }


@app.get("/transactions")
def get_transactions(limit: int = 50):
    """Get recent transaction history"""
    return {
        "transactions": logger.get_recent_transactions(limit)
    }


@app.get("/policy/logs")
def get_policy_logs(limit: int = 50):
    """Get recent policy decision logs"""
    return {
        "logs": logger.get_recent_policy_logs(limit)
    }


@app.get("/stats")
def get_statistics():
    """Get overall system statistics"""
    total_transactions = len(logger.transaction_logs)
    successful_transactions = len([t for t in logger.transaction_logs if t.status == "SUCCESS"])

    policy_actions = {}
    for log in logger.policy_logs:
        policy_actions[log.action] = policy_actions.get(log.action, 0) + 1

    return {
        "transactions": {
            "total": total_transactions,
            "successful": successful_transactions,
            "failed": total_transactions - successful_transactions
        },
        "policyActions": policy_actions,
        "totalAllocatedBudget": sum(a.dailyBudget for a in policy_engine.agents.values()),
        "totalSpent": sum(a.currentDailySpend for a in policy_engine.agents.values()),
        "serviceCount": len(policy_engine.services),
        "agentCount": len(policy_engine.agents)
    }


@app.post("/reset")
def reset_daily_budgets():
    """Reset all agents' daily spending (simulates a new day)"""
    for agent in policy_engine.agents.values():
        agent.currentDailySpend = 0.0

    return {
        "message": "All agents' daily spending has been reset to 0"
    }


@app.get("/graph/info")
def get_graph_info():
    """Get information about the graph architecture"""
    return {
        "architecture": "LangGraph StateGraph",
        "nodes": [
            "planner",
            "guardian",
            "executor",
            "feedback",
            "summarizer"
        ],
        "flow": "planner -> guardian -> executor -> (loop) -> feedback -> summarizer -> END",
        "state_model": "GraphState with StepRecord[]",
        "payment_enforcement": "Unified in Executor node via PaidToolWrapper"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
