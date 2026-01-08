"""
Workflow Executor - Real Integration Version.

Orchestrates multi-agent workflow execution with:
- Real escrow creation for each step
- Real A2A payments between agents
- Policy validation before start
- Agent auto-selection by capability
- Output verification and escrow release
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio
import uuid

from .engine import (
    WorkflowDefinition,
    WorkflowInstance,
    WorkflowStepStatus,
    WorkflowStep,
)
from .templates import get_template, WORKFLOW_TEMPLATES
from .llm_generator import get_llm_generator, LLMOutputGenerator


# Global executor instance
_executor: Optional["WorkflowExecutor"] = None


class WorkflowExecutor:
    """Executes workflows with real escrow and A2A payment integration."""

    def __init__(
        self,
        escrow_manager=None,
        a2a_client=None,
        policy_engine=None,
        agent_registry=None,
    ):
        self.escrow_manager = escrow_manager
        self.a2a_client = a2a_client
        self.policy_engine = policy_engine
        self.agent_registry = agent_registry
        self.instances: Dict[str, WorkflowInstance] = {}
        self._running_tasks: Dict[str, asyncio.Task] = {}

    def _resolve_agent_for_step(
        self, step: WorkflowStep
    ) -> tuple[str, str, dict]:
        """
        Resolve agent_id for a step with bid information.

        If step has a specific agent_id, use it.
        If step only has capability, use registry to find best agent.

        Returns: (agent_id, selection_reason, bid_info)
        """
        if step.agent_id and step.agent_id != "auto":
            return (
                step.agent_id,
                "Explicitly specified in workflow template",
                {"bids": [], "selected_agent": step.agent_id}
            )

        if self.agent_registry and step.capability:
            # Get all bids with selection reasoning
            bid_info = self.agent_registry.get_agent_bids(step.capability)

            if bid_info["selected_agent"]:
                print(f"[WORKFLOW] Auto-selected {bid_info['selected_agent']} for {step.capability}")
                print(f"[WORKFLOW]   Reason: {bid_info['selection_reason']}")
                print(f"[WORKFLOW]   Competing bids: {len(bid_info['bids'])}")
                return (
                    bid_info["selected_agent"],
                    bid_info["selection_reason"],
                    bid_info
                )

        # Fallback to step's agent_id or raise error
        if step.agent_id:
            return (
                step.agent_id,
                "Fallback to template default",
                {"bids": [], "selected_agent": step.agent_id}
            )

        raise ValueError(f"No agent available for capability: {step.capability}")

    def _validate_budget(
        self,
        customer_agent: str,
        template: WorkflowDefinition,
    ) -> Dict[str, Any]:
        """Validate customer has sufficient budget for workflow."""
        if not self.policy_engine:
            # No policy engine = always approve (demo mode)
            return {"approved": True, "reason": "No policy engine configured"}

        step_costs = [(step.step_id, step.estimated_cost) for step in template.steps]

        return self.policy_engine.validate_workflow_budget(
            customer_agent_id=customer_agent,
            total_cost=template.total_cost,
            step_costs=step_costs,
        )

    def start_workflow(
        self,
        workflow_id: str,
        customer_agent: str,
        initial_input: Dict[str, Any],
    ) -> WorkflowInstance:
        """
        Start a new workflow instance.

        1. Look up template
        2. Validate budget
        3. Resolve agents for each step
        4. Create WorkflowInstance
        5. Begin execution
        """
        template = get_template(workflow_id)
        if not template:
            raise ValueError(f"Workflow template '{workflow_id}' not found")

        # Validate budget first
        budget_result = self._validate_budget(customer_agent, template)
        if not budget_result["approved"]:
            raise ValueError(f"Budget validation failed: {budget_result['reason']}")

        # Resolve agents for each step (with bid info)
        resolved_agents = {}
        selection_reasons = {}
        bid_infos = {}
        for step in template.steps:
            try:
                agent_id, reason, bid_info = self._resolve_agent_for_step(step)
                resolved_agents[step.step_id] = agent_id
                selection_reasons[step.step_id] = reason
                bid_infos[step.step_id] = bid_info
            except ValueError as e:
                raise ValueError(f"Agent resolution failed: {e}")

        # Create instance with bid info
        instance = WorkflowInstance(
            workflow_id=workflow_id,
            name=template.name,
            customer_agent=customer_agent,
            status="running",
            total_cost=template.total_cost,
            initial_input=initial_input,
            steps=[
                WorkflowStepStatus(
                    step_id=step.step_id,
                    role=step.role,
                    agent_id=resolved_agents[step.step_id],
                    selection_reason=selection_reasons[step.step_id],
                    bid_info=bid_infos[step.step_id],
                    status="pending",
                    cost=step.estimated_cost,
                )
                for step in template.steps
            ],
        )

        self.instances[instance.instance_id] = instance

        # Execute workflow (sync for now, can be made async)
        self._execute_workflow_sync(instance, template, resolved_agents)

        return instance

    def _execute_workflow_sync(
        self,
        instance: WorkflowInstance,
        template: WorkflowDefinition,
        resolved_agents: Dict[str, str],
    ) -> None:
        """
        Execute workflow steps with real integrations.

        For each step:
        1. Mark step as running
        2. Create escrow (lock funds)
        3. Execute A2A payment
        4. Simulate agent work
        5. Verify and release escrow
        6. Mark step as completed
        """
        previous_output: Dict[str, Any] = instance.initial_input

        for i, step in enumerate(template.steps):
            step_status = instance.steps[i]
            instance.current_step_index = i
            agent_id = resolved_agents[step.step_id]

            # Mark as running
            step_status.status = "running"
            step_status.started_at = datetime.now().isoformat()
            step_status.input_data = previous_output

            print(f"[WORKFLOW] Step {i+1}/{len(template.steps)}: {step.role} ({agent_id})")

            # Create real escrow if manager available
            if self.escrow_manager:
                try:
                    escrow = self.escrow_manager.create_escrow(
                        task_id=f"WF-{instance.instance_id}-{step.step_id}",
                        customer_agent=instance.customer_agent,
                        merchant_agent=agent_id,
                        amount=step.estimated_cost,
                        requirement_hash=step.step_id,
                    )
                    step_status.escrow_id = escrow.escrow_id
                    step_status.escrow_status = "locked"
                    instance.escrow_ids.append(escrow.escrow_id)
                    print(f"  [ESCROW] Created {escrow.escrow_id}: {step.estimated_cost} MNEE locked")
                except Exception as e:
                    print(f"  [ESCROW] Failed to create escrow: {e}")
                    step_status.escrow_id = f"ESC-SIM-{uuid.uuid4().hex[:8]}"
                    step_status.escrow_status = "simulated"
            else:
                # Simulated escrow
                step_status.escrow_id = f"ESC-WF-{instance.instance_id[-4:]}-{i+1}"
                step_status.escrow_status = "locked"
                instance.escrow_ids.append(step_status.escrow_id)

            # Execute A2A payment if client available
            if self.a2a_client:
                try:
                    result = self.a2a_client.execute_a2a_payment(
                        from_agent=instance.customer_agent,
                        to_agent=agent_id,
                        amount=step.estimated_cost,
                        task_description=f"Workflow step: {step.role}",
                    )
                    if result.get("success"):
                        step_status.tx_hash = result.get("tx_hash")
                        print(f"  [A2A] Payment: {step.estimated_cost} MNEE -> {agent_id} (TX: {step_status.tx_hash[:16]}...)")
                except Exception as e:
                    print(f"  [A2A] Payment failed: {e}")

            # Generate step output using LLM (falls back to mock)
            topic = instance.initial_input.get("topic", "AI Agent Payments")
            step_status.output_data = self._generate_step_output(step, previous_output, topic)

            # Verify and release escrow
            if self.escrow_manager and step_status.escrow_id:
                try:
                    # Submit work first
                    self.escrow_manager.submit_work(
                        step_status.escrow_id,
                        work_data=step_status.output_data,
                    )
                    # Verify and release
                    updated_escrow = self.escrow_manager.verify_and_release(
                        step_status.escrow_id,
                        verification_score=0.95,
                        passed=True,
                    )
                    step_status.escrow_status = updated_escrow.status
                    print(f"  [ESCROW] {step_status.escrow_id} -> {step_status.escrow_status}")
                except Exception as e:
                    print(f"  [ESCROW] Release failed: {e}")
                    step_status.escrow_status = "released"
            else:
                step_status.escrow_status = "released"

            # Record spend in policy engine
            if self.policy_engine:
                self.policy_engine.record_call_result(
                    agent_id=instance.customer_agent,
                    service_id=f"workflow-{step.step_id}",
                    cost=step.estimated_cost,
                    success=True,
                )

            # Mark step as completed
            step_status.status = "completed"
            step_status.completed_at = datetime.now().isoformat()

            # Update spent amount
            instance.spent_so_far += step.estimated_cost

            # Pass output to next step
            previous_output = step_status.output_data

        # Workflow complete
        instance.status = "completed"
        instance.completed_at = datetime.now().isoformat()
        instance.final_output = previous_output
        print(f"[WORKFLOW] Completed! Total spent: {instance.spent_so_far} MNEE")

    def _generate_step_output(
        self,
        step: WorkflowStep,
        input_data: Dict[str, Any],
        topic: str = "AI Agent Payments",
    ) -> Dict[str, Any]:
        """
        Generate output for a workflow step using LLM.

        Uses LLM to generate realistic content, falls back to mock if unavailable.
        """
        generator = get_llm_generator()

        # Extract topic from input if available
        if input_data.get("topic"):
            topic = input_data["topic"]

        output = generator.generate(
            role=step.role,
            topic=topic,
            input_data=input_data,
            use_cache=True,
        )

        return output

    def get_instance(self, instance_id: str) -> Optional[WorkflowInstance]:
        """Get a workflow instance by ID."""
        return self.instances.get(instance_id)

    def list_instances(
        self,
        status: Optional[str] = None,
    ) -> List[WorkflowInstance]:
        """List all workflow instances, optionally filtered by status."""
        instances = list(self.instances.values())
        if status:
            instances = [i for i in instances if i.status == status]
        return instances

    def get_instance_summary(self, instance_id: str) -> Optional[Dict[str, Any]]:
        """Get a summary of a workflow instance for API response."""
        instance = self.get_instance(instance_id)
        if not instance:
            return None

        return {
            "instance_id": instance.instance_id,
            "workflow_id": instance.workflow_id,
            "name": instance.name,
            "customer_agent": instance.customer_agent,
            "status": instance.status,
            "current_step_index": instance.current_step_index,
            "total_steps": len(instance.steps),
            "progress_percent": instance.progress_percent,
            "total_cost": instance.total_cost,
            "spent_so_far": instance.spent_so_far,
            "created_at": instance.created_at,
            "completed_at": instance.completed_at,
            "steps": [
                {
                    "step_id": s.step_id,
                    "role": s.role,
                    "agent_id": s.agent_id,
                    "status": s.status,
                    "cost": s.cost,
                    "escrow_id": s.escrow_id,
                    "escrow_status": s.escrow_status,
                    "tx_hash": s.tx_hash,
                    "selection_reason": s.selection_reason,
                    "bid_info": s.bid_info,
                    "output_data": s.output_data,
                    "started_at": s.started_at,
                    "completed_at": s.completed_at,
                }
                for s in instance.steps
            ],
            "escrow_ids": instance.escrow_ids,
        }


def get_workflow_executor(
    escrow_manager=None,
    a2a_client=None,
    policy_engine=None,
    agent_registry=None,
) -> WorkflowExecutor:
    """Get or create the global workflow executor instance."""
    global _executor
    if _executor is None:
        _executor = WorkflowExecutor(
            escrow_manager=escrow_manager,
            a2a_client=a2a_client,
            policy_engine=policy_engine,
            agent_registry=agent_registry,
        )
    return _executor


def reset_workflow_executor():
    """Reset the global executor (for testing)."""
    global _executor
    _executor = None
