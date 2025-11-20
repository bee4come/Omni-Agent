import yaml
import os
from typing import Dict, Optional, List
from pydantic import BaseModel

class PolicyDecision(BaseModel):
    allowed: bool
    reason: str
    new_service_id: Optional[str] = None # For downgrades
    adjusted_amount: Optional[float] = None

class AgentConfig(BaseModel):
    id: str
    priority: str
    dailyBudget: float
    maxPerCall: float
    currentDailySpend: float = 0.0

class ServiceConfig(BaseModel):
    id: str
    unitPrice: float
    providerAddress: str
    active: bool

class PolicyEngine:
    def __init__(self, agents_path: str, services_path: str):
        self.agents: Dict[str, AgentConfig] = {}
        self.services: Dict[str, ServiceConfig] = {}
        self.load_configs(agents_path, services_path)

    def load_configs(self, agents_path: str, services_path: str):
        with open(agents_path, 'r') as f:
            data = yaml.safe_load(f)
            for a in data['agents']:
                self.agents[a['id']] = AgentConfig(**a)
        
        with open(services_path, 'r') as f:
            data = yaml.safe_load(f)
            for s in data['services']:
                self.services[s['id']] = ServiceConfig(**s)

    def check_policy(self, agent_id: str, service_id: str, quantity: int = 1) -> PolicyDecision:
        agent = self.agents.get(agent_id)
        service = self.services.get(service_id)

        if not agent:
            return PolicyDecision(allowed=False, reason=f"Agent {agent_id} not found")
        if not service:
            return PolicyDecision(allowed=False, reason=f"Service {service_id} not found")

        total_cost = service.unitPrice * quantity

        # 1. Check Max Per Call
        if total_cost > agent.maxPerCall:
             # Special logic: If Batch Agent exceeds cap, reject.
             if agent.id == "batch-agent":
                 return PolicyDecision(allowed=False, reason=f"Cost {total_cost} exceeds maxPerCall {agent.maxPerCall}")
        
        # 2. Check Daily Budget
        if agent.currentDailySpend + total_cost > agent.dailyBudget:
            # Downgrade Logic for LogArchive
            if service_id == "LOG_ARCHIVE":
                 return PolicyDecision(
                     allowed=True, 
                     reason="Budget low: Downgrading to summary only",
                     new_service_id="LOG_ARCHIVE_SUMMARY", # Hypothetical service
                     adjusted_amount=0.0 # Maybe free or cheaper?
                 )
            
            return PolicyDecision(allowed=False, reason=f"Budget exceeded. Remaining: {agent.dailyBudget - agent.currentDailySpend}")

        # 3. Priority Logic (Simplified)
        # If High Priority Agent needs budget, maybe we reject Low Priority? 
        # For now, just simple budget check.

        return PolicyDecision(allowed=True, reason="Approved")

    def record_spend(self, agent_id: str, amount: float):
        if agent_id in self.agents:
            self.agents[agent_id].currentDailySpend += amount

