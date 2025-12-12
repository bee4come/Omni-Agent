"""
LangGraph Workflow - Structured Agent orchestration with payment enforcement.

This module builds the complete execution graph:
  UserInput -> Planner -> Guardian -> Executor -> (loop) -> PolicyFeedback -> Summarizer -> END

Key architectural principles:
1. All state flows through GraphState (no hidden state)
2. Payment enforcement happens ONLY in Executor via PaidToolWrapper
3. Guardian provides pre-flight risk assessment
4. PolicyEngine enforces budget/priority rules
5. All decisions are recorded in StepRecord for auditing
"""

import os
from pathlib import Path
from typing import Dict, Any

from langgraph.graph import StateGraph, END, START

from .state import GraphState
from .nodes import (
    planner_node,
    guardian_node,
    executor_node,
    policy_feedback_node,
    summarizer_node
)
from .nodes.verifier import verifier_node, get_verifier
from .nodes.escrow import escrow_lock_node, escrow_release_node, get_escrow_manager
from .registry import get_registry

from payment.wrapper import PaidToolWrapper
from payment.client import PaymentClient
from payment.a2a_client import get_a2a_client
from policy.engine import PolicyEngine
from policy.logger import SystemLogger


def build_omni_agent_graph() -> StateGraph:
    """
    Build the complete Agent orchestration graph.

    Returns:
        Compiled StateGraph ready for invocation
    """
    print("[GRAPH] Building Omni-Agent orchestration graph...")

    # Initialize core services
    backend_dir = Path(__file__).parent.parent
    project_root = backend_dir.parent

    default_agents_path = project_root / "config" / "agents.yaml"
    default_services_path = project_root / "config" / "services.yaml"

    policy_engine = PolicyEngine(
        agents_path=os.getenv("POLICY_CONFIG_PATH", str(default_agents_path)),
        services_path=os.getenv("SERVICE_CONFIG_PATH", str(default_services_path))
    )

    payment_client = PaymentClient(policy_engine=policy_engine)
    logger = SystemLogger()

    paid_wrapper = PaidToolWrapper(
        policy_engine=policy_engine,
        payment_client=payment_client,
        logger=logger
    )

    # Initialize A2A client for agent-to-agent payments
    a2a_client = get_a2a_client()
    
    # Initialize Escrow Manager for trustless transactions
    escrow_manager = get_escrow_manager(a2a_client)
    
    # Initialize Verifier for task output verification
    verifier = get_verifier()
    
    # Initialize Agent Registry for dynamic discovery
    registry = get_registry()

    # Create workflow
    workflow = StateGraph(GraphState)

    # Register nodes - Escrow-Verify-Release protocol
    workflow.add_node("planner", planner_node)
    workflow.add_node("guardian", lambda state: guardian_node(state))
    workflow.add_node("escrow_lock", lambda state: escrow_lock_node(state, escrow_manager))
    workflow.add_node("executor", lambda state: executor_node(state, paid_wrapper, policy_engine, a2a_client))
    workflow.add_node("verifier", lambda state: verifier_node(state, verifier))
    workflow.add_node("escrow_release", lambda state: escrow_release_node(state, escrow_manager))
    workflow.add_node("feedback", policy_feedback_node)
    workflow.add_node("summarizer", summarizer_node)

    # Set entry point
    workflow.set_entry_point("planner")

    # Define flow: Planner -> Guardian -> EscrowLock -> Executor -> Verifier -> EscrowRelease
    workflow.add_edge("planner", "guardian")

    # Guardian -> EscrowLock or skip to feedback
    def after_guardian(state: GraphState) -> str:
        if state.guardian_block:
            return "feedback"
        return "escrow_lock"

    workflow.add_conditional_edges(
        "guardian",
        after_guardian,
        {
            "escrow_lock": "escrow_lock",
            "feedback": "feedback"
        }
    )

    # EscrowLock -> Executor
    workflow.add_edge("escrow_lock", "executor")

    # Executor -> Verifier or Feedback (if early exit)
    def after_executor(state: GraphState) -> str:
        if state.early_exit:
            return "feedback"
        return "verifier"

    workflow.add_conditional_edges(
        "executor",
        after_executor,
        {
            "verifier": "verifier",
            "feedback": "feedback"
        }
    )

    # Verifier -> EscrowRelease
    workflow.add_edge("verifier", "escrow_release")

    # EscrowRelease -> Feedback -> Summarizer -> END
    workflow.add_edge("escrow_release", "feedback")
    workflow.add_edge("feedback", "summarizer")
    workflow.add_edge("summarizer", END)

    print("[GRAPH] Graph built successfully")
    return workflow.compile()


class OmniAgentGraph:
    """
    High-level interface for the Agent graph.

    Provides a clean API for invoking the graph with user requests.
    """

    def __init__(self):
        self.graph = build_omni_agent_graph()
        print("[OMNI_AGENT_GRAPH] Initialized")

    def invoke(self, agent_id: str, user_message: str, task_id: str = None) -> Dict[str, Any]:
        """
        Execute the agent graph with a user request.

        Args:
            agent_id: Agent making the request (e.g., 'user-agent')
            user_message: User's goal/request
            task_id: Optional task ID (generated if not provided)

        Returns:
            Dict with:
                - final_answer: User-facing response
                - steps: List of executed steps with payment data
                - messages: Full conversation history
                - task_id: Task identifier
        """
        import uuid

        if task_id is None:
            task_id = str(uuid.uuid4())

        # Initialize state
        initial_state = GraphState(
            task_id=task_id,
            goal=user_message,
            active_agent=agent_id,
            messages=[{"role": "user", "content": user_message}]
        )

        print(f"\n{'=' * 70}")
        print(f"[OMNI_AGENT_GRAPH] Starting execution")
        print(f"  Agent: {agent_id}")
        print(f"  Task: {task_id}")
        print(f"  Goal: {user_message[:60]}...")
        print(f"{'=' * 70}\n")

        # Execute graph
        try:
            final_state = self.graph.invoke(initial_state)

            print(f"\n{'=' * 70}")
            print(f"[OMNI_AGENT_GRAPH] Execution complete")
            print(f"  Steps executed: {len(final_state.steps)}")
            print(f"  Successful: {len([s for s in final_state.steps if s.status == 'success'])}")
            print(f"  Failed: {len([s for s in final_state.steps if s.status in ['failed', 'denied']])}")
            print(f"{'=' * 70}\n")

            # Return structured result
            return {
                "final_answer": final_state.final_answer,
                "steps": [s.model_dump() for s in final_state.steps],
                "messages": final_state.messages,
                "task_id": task_id,
                "agent_id": agent_id,
                "success": len([s for s in final_state.steps if s.status == 'success']) > 0,
                "a2a_transfers": [t.model_dump() for t in final_state.a2a_transfers],
                "escrow_records": [e.model_dump() for e in final_state.escrow_records]
            }

        except Exception as e:
            print(f"\n[OMNI_AGENT_GRAPH] ERROR: {e}")
            return {
                "final_answer": f"Execution failed: {str(e)}",
                "steps": [],
                "messages": [{"role": "error", "content": str(e)}],
                "task_id": task_id,
                "agent_id": agent_id,
                "success": False,
                "error": str(e)
            }


# Singleton instance
_graph_instance = None


def get_agent_graph() -> OmniAgentGraph:
    """Get or create singleton graph instance"""
    global _graph_instance
    if _graph_instance is None:
        _graph_instance = OmniAgentGraph()
    return _graph_instance
