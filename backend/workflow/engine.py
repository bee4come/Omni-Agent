"""
Workflow Engine Models.

Defines the core data structures for multi-agent workflows:
- WorkflowStep: A single step in a workflow
- WorkflowDefinition: A workflow template
- WorkflowInstance: A running workflow instance
"""

from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime
import uuid


class WorkflowStep(BaseModel):
    """A single step in a workflow pipeline."""

    step_id: str
    agent_id: str  # Which agent executes this step
    role: str  # Human-readable role (Writer, Designer, etc.)
    capability: str  # Required capability (e.g., "data_analysis")
    estimated_cost: float  # MNEE cost for this step
    depends_on: List[str] = Field(default_factory=list)  # Previous step IDs


class WorkflowDefinition(BaseModel):
    """A workflow template defining the pipeline of agents."""

    workflow_id: str
    name: str
    description: str
    steps: List[WorkflowStep]

    @property
    def total_cost(self) -> float:
        """Calculate total cost of all steps."""
        return sum(step.estimated_cost for step in self.steps)

    @property
    def step_count(self) -> int:
        """Number of steps in the workflow."""
        return len(self.steps)


class WorkflowStepStatus(BaseModel):
    """Status of a single step in a running workflow."""

    step_id: str
    role: str
    agent_id: str
    status: Literal["pending", "running", "completed", "failed"] = "pending"
    escrow_id: Optional[str] = None
    escrow_status: Optional[str] = None
    tx_hash: Optional[str] = None  # On-chain transaction hash
    selection_reason: Optional[str] = None  # Why this agent was selected
    bid_info: Optional[Dict[str, Any]] = None  # All competing bids
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    cost: float = 0.0


class WorkflowInstance(BaseModel):
    """A running instance of a workflow."""

    instance_id: str = Field(default_factory=lambda: f"WF-{uuid.uuid4().hex[:8]}")
    workflow_id: str
    name: str
    customer_agent: str  # Who initiated and pays
    status: Literal["pending", "running", "completed", "failed"] = "pending"
    current_step_index: int = 0
    steps: List[WorkflowStepStatus] = Field(default_factory=list)
    escrow_ids: List[str] = Field(default_factory=list)
    initial_input: Dict[str, Any] = Field(default_factory=dict)
    final_output: Optional[Dict[str, Any]] = None
    total_cost: float = 0.0
    spent_so_far: float = 0.0
    created_at: str = Field(
        default_factory=lambda: datetime.now().isoformat()
    )
    completed_at: Optional[str] = None
    error: Optional[str] = None

    @property
    def progress_percent(self) -> float:
        """Calculate progress percentage."""
        if not self.steps:
            return 0.0
        completed = sum(1 for s in self.steps if s.status == "completed")
        return (completed / len(self.steps)) * 100

    def get_current_step(self) -> Optional[WorkflowStepStatus]:
        """Get the currently executing step."""
        if 0 <= self.current_step_index < len(self.steps):
            return self.steps[self.current_step_index]
        return None
