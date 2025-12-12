"""
Billing and Policy Models for MNEE Agent Cost & Billing Hub.

These models define the project-based budget hierarchy:
- ProjectPolicy: Team/project level budget and service allowlist
- AgentPolicy: Individual agent budget within a project
- UsageSnapshot: Real-time spending tracking
"""

from typing import List, Literal, Optional
from pydantic import BaseModel, Field


class ProjectPolicy(BaseModel):
    """
    Project-level policy defining budget and service access.

    Real-world use case:
    - project_id: "internal-chatbot", "nightly-etl", "report-generator"
    - Controls which services the project can access
    - Sets daily budget caps to prevent runaway spending
    """
    project_id: str
    name: str
    description: str = ""
    daily_budget_mnee: float
    hard_cap_mnee: float = float('inf')
    allow_services: List[str] = Field(default_factory=list)
    deny_services: List[str] = Field(default_factory=list)

    # Legacy fields for backward compatibility
    @property
    def id(self) -> str:
        return self.project_id

    @property
    def dailyBudget(self) -> float:
        return self.daily_budget_mnee

    @property
    def currentDailySpend(self) -> float:
        return 0.0  # Will be computed from UsageSnapshot


class AgentPolicy(BaseModel):
    """
    Agent-level policy within a project.

    Real-world use case:
    - agent_id: "user-agent", "batch-agent", "ops-agent"
    - Each agent has its own budget slice from project budget
    - Controls single transaction limits to prevent mistakes
    """
    agent_id: str
    project_id: str
    role: str  # e.g., "chatbot", "crawler", "analyst", "etl"
    daily_budget_mnee: float
    max_single_call_mnee: float
    priority: Literal["HIGH", "MEDIUM", "NORMAL", "LOW"] = "NORMAL"
    
    # Runtime tracking (not persisted)
    _current_daily_spend: float = 0.0

    class Config:
        underscore_attrs_are_private = True

    # Legacy fields for backward compatibility
    @property
    def id(self) -> str:
        return self.agent_id

    @property
    def dailyBudget(self) -> float:
        return self.daily_budget_mnee

    @property
    def maxPerCall(self) -> float:
        return self.max_single_call_mnee

    @property
    def currentDailySpend(self) -> float:
        return self._current_daily_spend
    
    @currentDailySpend.setter
    def currentDailySpend(self, value: float):
        self._current_daily_spend = value


class UsageSnapshot(BaseModel):
    """
    Real-time spending tracker for project/agent.

    Tracks:
    - Today's spending
    - Total historical spending
    - Last reset timestamp (for daily budget reset)
    """
    project_id: str
    agent_id: str
    spent_today_mnee: float = 0.0
    spent_total_mnee: float = 0.0
    last_reset_timestamp: str = ""
    transaction_count_today: int = 0


class PolicyDecision(BaseModel):
    """
    Policy engine decision result.

    Actions:
    - ALLOW: Within budget, proceed
    - DENY: Over budget or not allowed
    - DOWNGRADE: Reduce quantity to fit budget
    """
    action: Literal["ALLOW", "DENY", "DOWNGRADE"]
    approved_quantity: int
    risk_level: Literal["RISK_OK", "RISK_REVIEW", "RISK_BLOCK"]
    reason: str

    # Additional context for debugging
    project_budget_remaining: Optional[float] = None
    agent_budget_remaining: Optional[float] = None
