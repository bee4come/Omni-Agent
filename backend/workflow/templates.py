"""
Pre-defined Workflow Templates.

Demo workflows for the hackathon presentation:
1. Content Creation Pipeline: Writer -> Designer -> Reviewer
2. Data Analysis Pipeline: Collector -> Analyzer -> Reporter
"""

from typing import Dict, Optional
from .engine import WorkflowDefinition, WorkflowStep


# Content Creation Pipeline
# Story: Create a marketing report with text and visuals
CONTENT_CREATION = WorkflowDefinition(
    workflow_id="content-creation",
    name="Content Creation Pipeline",
    description="Writer -> Designer -> Reviewer: Create content with text, visuals, and review",
    steps=[
        WorkflowStep(
            step_id="write",
            agent_id="startup-analyst",
            role="Writer",
            capability="data_analysis",
            estimated_cost=2.0,
            depends_on=[],
        ),
        WorkflowStep(
            step_id="design",
            agent_id="startup-designer",
            role="Designer",
            capability="image_gen",
            estimated_cost=3.0,
            depends_on=["write"],
        ),
        WorkflowStep(
            step_id="review",
            agent_id="startup-archivist",
            role="Reviewer",
            capability="log_archive",
            estimated_cost=0.5,
            depends_on=["design"],
        ),
    ],
)


# Data Analysis Pipeline
# Story: Collect data, analyze it, and generate a report
DATA_ANALYSIS = WorkflowDefinition(
    workflow_id="data-analysis",
    name="Data Analysis Pipeline",
    description="Collector -> Analyzer -> Reporter: Gather data, analyze, and report findings",
    steps=[
        WorkflowStep(
            step_id="collect",
            agent_id="startup-archivist",
            role="Collector",
            capability="log_archive",
            estimated_cost=0.2,
            depends_on=[],
        ),
        WorkflowStep(
            step_id="analyze",
            agent_id="startup-analyst",
            role="Analyzer",
            capability="data_analysis",
            estimated_cost=1.5,
            depends_on=["collect"],
        ),
        WorkflowStep(
            step_id="report",
            agent_id="startup-designer",
            role="Reporter",
            capability="image_gen",
            estimated_cost=2.0,
            depends_on=["analyze"],
        ),
    ],
)


# Registry of all templates
WORKFLOW_TEMPLATES: Dict[str, WorkflowDefinition] = {
    "content-creation": CONTENT_CREATION,
    "data-analysis": DATA_ANALYSIS,
}


def get_template(workflow_id: str) -> Optional[WorkflowDefinition]:
    """Get a workflow template by ID."""
    return WORKFLOW_TEMPLATES.get(workflow_id)


def list_templates() -> list:
    """List all available templates with summary info."""
    return [
        {
            "workflow_id": t.workflow_id,
            "name": t.name,
            "description": t.description,
            "step_count": t.step_count,
            "total_cost": t.total_cost,
            "steps": [
                {"role": s.role, "agent_id": s.agent_id, "cost": s.estimated_cost}
                for s in t.steps
            ],
        }
        for t in WORKFLOW_TEMPLATES.values()
    ]
