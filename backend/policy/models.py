from typing import List, Literal, Optional
from pydantic import BaseModel, Field

class ProjectPolicy(BaseModel):
    project_id: str
    name: str
    daily_budget_mnee: float
    hard_cap_mnee: float = float('inf')
    allow_services: List[str] = Field(default_factory=list)
    deny_services: List[str] = Field(default_factory=list)

class AgentPolicy(BaseModel):
    agent_id: str
    project_id: str
    role: str # e.g., "chatbot", "crawler", "analyst"
    daily_budget_mnee: float
    max_single_call_mnee: float
    priority: Literal["HIGH", "MEDIUM", "NORMAL", "LOW"] = "NORMAL"

class UsageSnapshot(BaseModel):
    project_id: str
    agent_id: str
    spent_today_mnee: float = 0.0
    spent_total_mnee: float = 0.0
    last_reset_timestamp: str = ""

class PolicyDecision(BaseModel):
    action: Literal["ALLOW", "DENY", "DOWNGRADE"]
    approved_quantity: int
    risk_level: Literal["RISK_OK", "RISK_REVIEW", "RISK_BLOCK"]
    reason: str
