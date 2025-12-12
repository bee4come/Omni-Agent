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

class A2APaymentRecord(BaseModel):
    """Record of an A2A payment during task delegation"""
    from_agent: str
    to_agent: str
    amount: float
    task_description: str
    tx_hash: Optional[str] = None
    success: bool = False


class EscrowStatus:
    """Escrow state constants for trustless Agent transactions"""
    CREATED = "created"      # Escrow created, funds locked
    SUBMITTED = "submitted"  # Work submitted by merchant
    VERIFYING = "verifying"  # Under verification
    RELEASED = "released"    # Funds released to merchant
    REFUNDED = "refunded"    # Funds returned to customer
    DISPUTED = "disputed"    # In dispute resolution


class EscrowRecord(BaseModel):
    """
    Record of an Escrow transaction in the Agent labor market.
    
    Implements the Escrow-Verify-Release protocol:
    1. Customer locks funds in escrow
    2. Merchant performs work
    3. Verifier validates output
    4. Funds released or refunded based on verification
    """
    escrow_id: str = Field(..., description="Unique escrow identifier")
    task_id: str = Field(..., description="Associated task ID")
    
    # Participants
    customer_agent: str = Field(..., description="Agent paying for service")
    merchant_agent: str = Field(..., description="Agent providing service")
    verifier_agent: Optional[str] = Field(None, description="Agent verifying output")
    
    # Financial
    amount: float = Field(..., description="Locked amount in MNEE")
    fee: float = Field(0.0, description="Platform/verification fee")
    
    # State
    status: str = Field("created", description="Current escrow status")
    
    # Timestamps
    created_at: Optional[str] = None
    submitted_at: Optional[str] = None
    verified_at: Optional[str] = None
    released_at: Optional[str] = None
    
    # Work evidence
    work_ipfs_cid: Optional[str] = Field(None, description="IPFS CID of submitted work")
    requirement_hash: Optional[str] = Field(None, description="Hash of task requirements")
    
    # Verification
    verification_score: float = Field(0.0, description="Verification score (0-1)")
    verification_passed: bool = Field(False, description="Whether verification passed")
    
    # On-chain references
    lock_tx_hash: Optional[str] = Field(None, description="TX hash of fund locking")
    release_tx_hash: Optional[str] = Field(None, description="TX hash of fund release")
    
    # Dispute
    dispute_reason: Optional[str] = None
    dispute_resolution: Optional[str] = None


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
    
    # A2A payment info (if this step was delegated)
    a2a_payment: Optional[A2APaymentRecord] = None
    
    # Escrow info (for trustless transactions)
    escrow_id: Optional[str] = None
    escrow_status: Optional[str] = None

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
    active_agent: Literal["user-agent", "startup-designer", "startup-analyst", "startup-archivist"] = Field(
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
    
    # A2A payment records
    a2a_transfers: List[A2APaymentRecord] = Field(
        default_factory=list,
        description="All A2A payments made during this task"
    )
    
    # Escrow records for trustless transactions
    escrow_records: List[EscrowRecord] = Field(
        default_factory=list,
        description="All escrow transactions in this task"
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

