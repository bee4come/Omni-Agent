from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from agents.omni_agent import OmniAgent
from agents.merchant_agent import router as merchant_router
import os
from dotenv import load_dotenv

load_dotenv()

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="MNEE Nexus / Omni-Agent API",
    description="Programmable Payment Orchestrator for AI Agents",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For hackathon/demo purposes, allow all. In prod, specify domains.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(merchant_router)

omni_agent = OmniAgent()

class ChatRequest(BaseModel):
    agent_id: str
    message: str

class BudgetUpdateRequest(BaseModel):
    daily_budget: Optional[float] = None
    max_per_call: Optional[float] = None

@app.get("/")
def root():
    return {
        "name": "MNEE Nexus / Omni-Agent",
        "version": "1.0.0",
        "status": "running"
    }

@app.post("/chat")
def chat(request: ChatRequest):
    """
    Send a message to an agent and get a response.
    The agent will use paid tools as needed, respecting budget and policy.
    """
    try:
        result = omni_agent.run(request.agent_id, request.message)
        return {
            "response": result['output'],
            "agent_id": request.agent_id,
            "payment_results": result.get('payment_results', [])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/treasury")
def get_treasury_status():
    """
    Get the overall treasury status including all agents' budgets and spending.
    """
    agents_data = {}
    for agent_id, agent in omni_agent.policy_engine.agents.items():
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
        "totalAllocated": sum(a.dailyBudget for a in omni_agent.policy_engine.agents.values()),
        "totalSpent": sum(a.currentDailySpend for a in omni_agent.policy_engine.agents.values())
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
            for agent in omni_agent.policy_engine.agents.values()
        ]
    }

@app.get("/agents/{agent_id}")
def get_agent(agent_id: str):
    """Get detailed info about a specific agent"""
    agent = omni_agent.policy_engine.agents.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")
    
    return {
        "id": agent.id,
        "priority": agent.priority,
        "dailyBudget": agent.dailyBudget,
        "maxPerCall": agent.maxPerCall,
        "currentDailySpend": agent.currentDailySpend,
        "remainingBudget": agent.dailyBudget - agent.currentDailySpend,
        "transactions": omni_agent.logger.get_agent_transactions(agent_id),
        "totalSpent": omni_agent.logger.get_total_spent_by_agent(agent_id)
    }

@app.put("/agents/{agent_id}/budget")
def update_agent_budget(agent_id: str, request: BudgetUpdateRequest):
    """Update an agent's budget configuration"""
    agent = omni_agent.policy_engine.agents.get(agent_id)
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
            for service in omni_agent.policy_engine.services.values()
        ]
    }

@app.get("/services/{service_id}")
def get_service(service_id: str):
    """Get detailed info about a specific service"""
    service = omni_agent.policy_engine.services.get(service_id)
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
        "transactions": omni_agent.logger.get_service_transactions(service_id),
        "totalRevenue": omni_agent.logger.get_total_revenue_by_service(service_id)
    }

@app.get("/transactions")
def get_transactions(limit: int = 50):
    """Get recent transaction history"""
    return {
        "transactions": omni_agent.logger.get_recent_transactions(limit)
    }

@app.get("/policy/logs")
def get_policy_logs(limit: int = 50):
    """Get recent policy decision logs"""
    return {
        "logs": omni_agent.logger.get_recent_policy_logs(limit)
    }

@app.get("/stats")
def get_statistics():
    """Get overall system statistics"""
    total_transactions = len(omni_agent.logger.transaction_logs)
    successful_transactions = len([t for t in omni_agent.logger.transaction_logs if t.status == "SUCCESS"])
    
    policy_actions = {}
    for log in omni_agent.logger.policy_logs:
        policy_actions[log.action] = policy_actions.get(log.action, 0) + 1
    
    return {
        "transactions": {
            "total": total_transactions,
            "successful": successful_transactions,
            "failed": total_transactions - successful_transactions
        },
        "policyActions": policy_actions,
        "totalAllocatedBudget": sum(a.dailyBudget for a in omni_agent.policy_engine.agents.values()),
        "totalSpent": sum(a.currentDailySpend for a in omni_agent.policy_engine.agents.values()),
        "serviceCount": len(omni_agent.policy_engine.services),
        "agentCount": len(omni_agent.policy_engine.agents)
    }

@app.post("/reset")
def reset_daily_budgets():
    """Reset all agents' daily spending (simulates a new day)"""
    for agent in omni_agent.policy_engine.agents.values():
        agent.currentDailySpend = 0.0
    
    return {
        "message": "All agents' daily spending has been reset to 0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
