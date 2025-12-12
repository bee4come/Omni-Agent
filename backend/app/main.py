from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from agents.omni_agent import OmniAgent
from agents.merchant_agent import router as merchant_router
from payment.a2a_client import get_a2a_client
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
            "steps": result.get('steps', []),
            "a2a_transfers": result.get('a2a_transfers', []),
            "escrow_records": result.get('escrow_records', []),
            "guardian": {
                "reasoning": result.get("guardian_reasoning"),
                "risk_score": result.get("guardian_risk_score"),
                "blocked": result.get("guardian_block")
            }
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

# ============================================================
# A2A (Agent-to-Agent) Payment Endpoints
# ============================================================

class A2APaymentRequest(BaseModel):
    from_agent: str
    to_agent: str
    amount: float
    task_description: str

@app.post("/a2a/pay")
def execute_a2a_payment(request: A2APaymentRequest):
    """
    Execute an Agent-to-Agent payment on-chain.
    
    This creates a real MNEE transfer between agent wallets.
    """
    a2a_client = get_a2a_client()
    result = a2a_client.execute_a2a_payment(
        from_agent=request.from_agent,
        to_agent=request.to_agent,
        amount=request.amount,
        task_description=request.task_description
    )
    
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Payment failed"))
    
    return result

@app.get("/a2a/transfers")
def get_a2a_transfers(count: int = 20):
    """Get recent A2A transfers for visualization"""
    a2a_client = get_a2a_client()
    return {
        "transfers": a2a_client.get_recent_transfers(count),
        "total_count": a2a_client.get_transfer_count()
    }

@app.get("/a2a/balances")
def get_agent_wallet_balances():
    """Get all agent wallet balances from the smart contract"""
    a2a_client = get_a2a_client()
    balances = a2a_client.get_all_agent_balances()
    
    return {
        "balances": balances,
        "total": sum(balances.values())
    }

@app.get("/a2a/agent/{agent_id}")
def get_agent_wallet_info(agent_id: str):
    """Get detailed info about an agent's wallet"""
    a2a_client = get_a2a_client()
    info = a2a_client.get_agent_info(agent_id)
    
    if not info.get("registered"):
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found in wallet")
    
    return info

# ============================================================
# Agent Registry Endpoints (Decentralized Labor Market)
# ============================================================

from agents.registry import get_registry, AgentCard

@app.get("/registry/agents")
def list_registered_agents():
    """List all agents in the registry with their capabilities and pricing"""
    registry = get_registry()
    agents = registry.get_all_agents()
    return {
        "agents": [a.model_dump() for a in agents],
        "market_stats": registry.get_market_stats()
    }

@app.get("/registry/agent/{agent_id}")
def get_agent_card(agent_id: str):
    """Get a specific agent's card with capabilities and reputation"""
    registry = get_registry()
    agent = registry.get(agent_id)
    
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found in registry")
    
    return agent.model_dump()

@app.get("/registry/find")
def find_agents_by_capability(capability: str):
    """Find agents that can handle a specific capability"""
    registry = get_registry()
    agents = registry.find_by_capability(capability)
    return {
        "capability": capability,
        "agents": [a.model_dump() for a in agents],
        "count": len(agents)
    }

@app.get("/registry/select")
def select_best_agent(capability: str, price_weight: float = 0.4, reputation_weight: float = 0.4):
    """Select the best agent for a capability based on weighted scoring"""
    registry = get_registry()
    success_weight = 1.0 - price_weight - reputation_weight
    
    agent = registry.select_best_agent(
        capability=capability,
        price_weight=price_weight,
        reputation_weight=reputation_weight,
        success_weight=success_weight
    )
    
    if not agent:
        raise HTTPException(status_code=404, detail=f"No agents found for capability: {capability}")
    
    return {
        "selected_agent": agent.model_dump(),
        "selection_criteria": {
            "capability": capability,
            "price_weight": price_weight,
            "reputation_weight": reputation_weight,
            "success_weight": success_weight
        }
    }

# ============================================================
# Escrow Endpoints (Trustless Transactions)
# ============================================================

from agents.nodes.escrow import get_escrow_manager

@app.get("/escrow/list")
def list_escrows():
    """List all escrow transactions"""
    escrow_manager = get_escrow_manager()
    escrows = list(escrow_manager.escrows.values())
    
    return {
        "escrows": [e.model_dump() for e in escrows],
        "total_count": len(escrows),
        "by_status": {
            "created": len([e for e in escrows if e.status == "created"]),
            "submitted": len([e for e in escrows if e.status == "submitted"]),
            "verifying": len([e for e in escrows if e.status == "verifying"]),
            "released": len([e for e in escrows if e.status == "released"]),
            "refunded": len([e for e in escrows if e.status == "refunded"]),
            "disputed": len([e for e in escrows if e.status == "disputed"]),
        }
    }

@app.get("/escrow/{escrow_id}")
def get_escrow(escrow_id: str):
    """Get details of a specific escrow"""
    escrow_manager = get_escrow_manager()
    escrow = escrow_manager.get_escrow(escrow_id)
    
    if not escrow:
        raise HTTPException(status_code=404, detail=f"Escrow {escrow_id} not found")
    
    return escrow.model_dump()

class DisputeRequest(BaseModel):
    reason: str

@app.post("/escrow/{escrow_id}/dispute")
def raise_escrow_dispute(escrow_id: str, request: DisputeRequest):
    """Raise a dispute for an escrow transaction"""
    escrow_manager = get_escrow_manager()
    
    try:
        escrow = escrow_manager.raise_dispute(escrow_id, request.reason)
        return {
            "message": "Dispute raised successfully",
            "escrow": escrow.model_dump()
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
