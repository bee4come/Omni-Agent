"""
Summarizer Node - Synthesizes final response from execution results.

The Summarizer is the last node before END:
1. Aggregates all step results
2. Formats output for user display
3. Includes payment/transaction information
4. Generates final_answer field
"""

from ..state import GraphState


def summarizer_node(state: GraphState) -> GraphState:
    """
    Summarizer node: Generate final user-facing response.

    Flow:
    1. Scan all executed steps
    2. Format successful results
    3. Include payment information
    4. Generate concise summary
    5. Set final_answer

    Args:
        state: Current GraphState

    Returns:
        Updated GraphState with final_answer filled
    """
    print(f"\n[SUMMARIZER_NODE] Synthesizing from {len(state.steps)} steps")

    if not state.steps:
        state.final_answer = "No operations were performed."
        return state

    # Separate successful and failed steps
    successful_steps = [s for s in state.steps if s.status == "success"]
    failed_steps = [s for s in state.steps if s.status in ["failed", "denied"]]

    print(f"[SUMMARIZER_NODE] Successful: {len(successful_steps)}, Failed: {len(failed_steps)}")

    # Build output
    output_lines = []

    # Add successful results
    if successful_steps:
        output_lines.append("[Results]\n")

        for step in successful_steps:
            # Format based on tool type
            if step.tool_name == "get_quote":
                quote_id = step.output.get("quoteId", "N/A") if step.output else "N/A"
                price = step.output.get("unitPriceMNEE", "N/A") if step.output else "N/A"
                output_lines.append(f"Quote Received: {quote_id}")
                output_lines.append(f"  Price: {price} MNEE")

            elif step.tool_name == "purchase_service":
                status = step.output.get("status", "N/A") if step.output else "N/A"
                output_lines.append(f"Purchase: {status}")
                if step.output and "data" in step.output:
                    data = step.output["data"]
                    if "imageUrl" in data:
                        output_lines.append(f"  Image: {data['imageUrl']}")
                    if "reportUrl" in data:
                        output_lines.append(f"  Report: {data['reportUrl']}")

            elif step.tool_name == "image_gen":
                url = step.output.get("imageUrl", "N/A") if step.output else "N/A"
                mock_note = " (Mock)" if (step.output and step.output.get("mock")) else ""
                output_lines.append(f"Image Generated{mock_note}")
                output_lines.append(f"  URL: {url}")

            elif step.tool_name == "price_oracle":
                if step.output:
                    base = step.output.get("base", "N/A")
                    quote = step.output.get("quote", "N/A")
                    price = step.output.get("price", "N/A")
                    mock_note = " (Mock)" if step.output.get("mock") else ""
                    output_lines.append(f"Price Query{mock_note}: {base}/{quote} = {price}")

            elif step.tool_name == "batch_compute":
                if step.output:
                    job_id = step.output.get("jobId", "N/A")
                    status = step.output.get("status", "N/A")
                    mock_note = " (Mock)" if step.output.get("mock") else ""
                    output_lines.append(f"Batch Job{mock_note}: {job_id}")
                    output_lines.append(f"  Status: {status}")

            elif step.tool_name == "log_archive":
                if step.output:
                    storage_id = step.output.get("storageId", "N/A")
                    mock_note = " (Mock)" if step.output.get("mock") else ""
                    output_lines.append(f"Logs Archived{mock_note}")
                    output_lines.append(f"  Storage ID: {storage_id}")

            elif step.tool_name == "respond":
                if step.output:
                    output_lines.append(step.output.get("response", "OK"))

            else:
                output_lines.append(f"{step.description}: Completed")

            # Add payment info if paid
            if step.tx_hash:
                output_lines.append(f"  Payment TX: {step.tx_hash[:16]}...")
            # Get amount from output if available
            amount = step.output.get('amount_mnee', 0) if step.output else 0
            if amount:
                output_lines.append(f"  Cost: {amount} MNEE")

            output_lines.append("")

    # Add failure summary if any
    if failed_steps:
        output_lines.append("\n[Failures]")
        for step in failed_steps:
            output_lines.append(f"- {step.description}: {step.error}")

        output_lines.append("")

    # Add financial summary - extract from output dict
    def get_step_amount(s):
        if s.output and isinstance(s.output, dict):
            return s.output.get('amount_mnee', 0) or 0
        return 0
    total_spent = sum(get_step_amount(s) for s in successful_steps)
    if total_spent > 0:
        output_lines.append(f"\n[Financial Summary]")
        output_lines.append(f"Total Spent: {total_spent:.2f} MNEE")
        output_lines.append(f"Transactions: {len([s for s in successful_steps if s.tx_hash])}")

    # Set final answer
    state.final_answer = "\n".join(output_lines)

    # Add to message history
    state.messages.append({
        "role": "assistant",
        "content": state.final_answer
    })

    print("[SUMMARIZER_NODE] Final answer generated")

    return state
