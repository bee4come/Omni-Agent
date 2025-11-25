"""
Structured state definitions for LangGraph-based Agent orchestration.

This module defines the core state structures that flow through the Agent graph,
ensuring all decisions, payments, and policy enforcement are fully traceable.
"""

from typing import Literal, List, Dict, Any, Optional
from pydantic import BaseModel, Field

class PlanStep(BaseModel):
    step_id: str
    description: str
    agent_id: Literal["user-agent", "batch-agent", "ops-agent", "merchant-agent", "customer-agent", "startup-designer", "startup-analyst", "startup-archivist"]
    service_id: Optional[str] = None   # e.g. "IMAGE_GEN_PREMIUM"
    tool_name: str              # Tool name registered in backend
    estimated_quantity: int
    max_mnee_cost: float
    params: Dict[str, Any]

class StepRecord(BaseModel):
    step_id: str
    description: Optional[str] = None
    agent_id: str
    project_id: Optional[str] = None
    service_id: Optional[str] = None
    tool_name: Optional[str] = None
    input: Dict[str, Any] = Field(default_factory=dict)
    output: Optional[Dict[str, Any]] = None
    payment_id: Optional[str] = None
    service_call_hash: Optional[str] = None
    tx_hash: Optional[str] = None
    policy_action: Optional[Literal["ALLOW", "DENY", "DOWNGRADE"]] = None
    risk_level: Optional[Literal["RISK_OK", "RISK_REVIEW", "RISK_BLOCK"]] = None
    error: Optional[str] = None
    status: Literal["pending", "executing", "success", "failed", "denied"] = "pending"

    params: Dict[str, Any] = Field(default_factory=dict, description="Tool parameters")


class Plan(BaseModel):
    """Wrapper for a list of PlanSteps, used for PydanticOutputParser"""
    steps: List[PlanStep] = Field(..., description="The ordered list of steps to execute")


class GraphState(BaseModel):
    # User context
    user_id: Optional[str] = Field(None, description="User identifier")
    task_id: str = Field(..., description="Unique task identifier for this execution")
    goal: str = Field(..., description="User's original request/goal")

    # Agent routing
    active_agent: Literal["user-agent", "batch-agent", "ops-agent", "merchant-agent", "customer-agent", "startup-designer", "startup-analyst", "startup-archivist"] = Field(
        "user-agent", description="Currently active agent"
    )

    # Conversation history
    messages: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Chat history"
    )

    # Execution plan
    plan: List[PlanStep] = Field(
        default_factory=list,
        description="List of PlanSteps"
    )
    current_step_index: int = Field(0, description="Index of currently executing step")

    # Execution records
    steps: List[StepRecord] = Field(
        default_factory=list,
        description="Complete history"
    )

    # Final output
    final_answer: Optional[str] = Field(None, description="Final response to user")

    # Control flags
    guardian_block: bool = Field(False, description="Set to True if Guardian blocked execution")
    guardian_reasoning: Optional[str] = Field(None, description="Explanation from the AI Guardian")
    guardian_risk_score: int = Field(0, description="Risk score (0-10) assigned by Guardian")
    early_exit: bool = Field(False, description="Set to True to skip remaining steps")

    # Metadata
    treasury_balance: Optional[float] = Field(None, description="Current treasury MNEE balance")
    
    class Config:
        arbitrary_types_allowed = True

