"""
Policy Feedback Node - Handles policy rejections and provides user feedback.

When policy/risk blocks a payment, this node:
1. Aggregates all denial reasons
2. Suggests alternatives (e.g., downgraded services)
3. Provides budget status information
4. Adds user-friendly messages to conversation
"""

from ..state import GraphState


def policy_feedback_node(state: GraphState) -> GraphState:
    """
    Policy Feedback node: Generate user-friendly feedback for denials.

    Flow:
    1. Scan steps for denied/failed steps
    2. Aggregate reasons
    3. Check if there were downgrades
    4. Add informative message to conversation

    Args:
        state: Current GraphState

    Returns:
        Updated GraphState with feedback messages
    """
    print(f"\n[POLICY_FEEDBACK_NODE] Analyzing {len(state.steps)} executed steps")

    # Collect all denied/failed steps
    denied_steps = [s for s in state.steps if s.status in ['denied', 'failed']]

    if not denied_steps:
        print("[POLICY_FEEDBACK_NODE] No denied steps, nothing to report")
        return state

    print(f"[POLICY_FEEDBACK_NODE] Found {len(denied_steps)} denied/failed steps")

    # Build feedback message
    feedback_lines = [
        "\n[Policy Feedback]",
        ""
    ]

    for step in denied_steps:
        if step.policy_action == "DENY":
            feedback_lines.append(f"Blocked: {step.description}")
            feedback_lines.append(f"  Reason: {step.error}")
            feedback_lines.append(f"  Risk Level: {step.risk_level}")

            # Suggest alternatives
            if "budget" in step.error.lower():
                feedback_lines.append(f"  Suggestion: Check your daily budget with /treasury")
            elif "burst" in step.error.lower():
                feedback_lines.append(f"  Suggestion: Wait a moment before retrying")
            elif "priority" in step.error.lower():
                feedback_lines.append(f"  Suggestion: Contact admin to upgrade agent priority")

        else:
            # Failed execution
            feedback_lines.append(f"Failed: {step.description}")
            feedback_lines.append(f"  Error: {step.error}")

        feedback_lines.append("")

    # Check budget status - extract from output dict
    def get_step_amount(s):
        if s.output and isinstance(s.output, dict):
            return s.output.get('amount_mnee', 0) or 0
        return 0
    total_spent = sum(get_step_amount(s) for s in state.steps if s.status == "success")
    if total_spent > 0:
        feedback_lines.append(f"Total spent this session: {total_spent:.2f} MNEE")

    # Add to messages
    feedback_text = "\n".join(feedback_lines)
    state.messages.append({
        "role": "system",
        "content": feedback_text
    })

    print("[POLICY_FEEDBACK_NODE] Feedback added to conversation")

    return state
