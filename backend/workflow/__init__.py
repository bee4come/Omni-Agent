"""
Workflow Engine for Multi-Agent Collaboration.

Enables defining and executing workflow chains where multiple agents
collaborate on complex tasks with A2A payments and escrow handoffs.
"""

from .engine import (
    WorkflowStep,
    WorkflowDefinition,
    WorkflowInstance,
    WorkflowStepStatus,
)
from .templates import WORKFLOW_TEMPLATES, get_template
from .executor import WorkflowExecutor, get_workflow_executor

__all__ = [
    "WorkflowStep",
    "WorkflowDefinition",
    "WorkflowInstance",
    "WorkflowStepStatus",
    "WORKFLOW_TEMPLATES",
    "get_template",
    "WorkflowExecutor",
    "get_workflow_executor",
]
