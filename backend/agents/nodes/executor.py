from typing import Any, Dict, Callable, Optional
from ..state import GraphState, StepRecord, PlanStep, A2APaymentRecord

# We need a way to resolve tool_name to a function and wrapper.
# In a real app, these would be injected or imported from a registry.
# For now, we'll assume they are passed in or we import a registry.

def executor_node(state: GraphState, tool_registry: Any, policy_engine: Any = None, a2a_client: Any = None) -> GraphState:
    """
    Executor Node: Iterates through the plan and executes tools.
    
    It uses the PlanStep data to call the PaidToolWrapper.
    It updates state.steps with the results (StepRecord).
    """
    print(f"\n[EXECUTOR_NODE] Executing plan (Current Index: {state.current_step_index})")
    
    # Loop through steps starting from current_index
    while state.current_step_index < len(state.plan):
        raw_step = state.plan[state.current_step_index]
        # Handle both dict and object (Pydantic compatibility)
        if isinstance(raw_step, dict):
            step = PlanStep(**raw_step)
        else:
            step = raw_step
            
        print(f"  > Step {state.current_step_index + 1}: {step.tool_name} ({step.description})")
        
        # Look up Project ID
        project_id = None
        if policy_engine:
            agent_policy = policy_engine.agents.get(step.agent_id)
            if agent_policy:
                project_id = agent_policy.project_id

        # 1. A2A Payment - if task is delegated to a different agent
        a2a_payment_record = None
        if a2a_client and step.agent_id != state.active_agent:
            # This is a delegation: active_agent pays step.agent_id
            delegation_cost = step.max_mnee_cost * 0.1  # 10% delegation fee
            if delegation_cost < 0.01:
                delegation_cost = 0.01  # Minimum fee
                
            print(f"    [A2A] Delegating: {state.active_agent} -> {step.agent_id} ({delegation_cost:.3f} MNEE)")
            
            try:
                a2a_result = a2a_client.execute_a2a_payment(
                    from_agent=state.active_agent,
                    to_agent=step.agent_id,
                    amount=delegation_cost,
                    task_description=step.description
                )
                
                a2a_payment_record = A2APaymentRecord(
                    from_agent=state.active_agent,
                    to_agent=step.agent_id,
                    amount=delegation_cost,
                    task_description=step.description,
                    tx_hash=a2a_result.get("tx_hash"),
                    success=a2a_result.get("success", False)
                )
                
                # Add to state's a2a_transfers list
                state.a2a_transfers.append(a2a_payment_record)
                
                if a2a_result.get("success"):
                    print(f"    [A2A] Payment success: TX {a2a_result.get('tx_hash', '')[:16]}...")
                else:
                    print(f"    [A2A] Payment failed: {a2a_result.get('error')}")
                    
            except Exception as e:
                print(f"    [A2A] Payment error: {e}")
                a2a_payment_record = A2APaymentRecord(
                    from_agent=state.active_agent,
                    to_agent=step.agent_id,
                    amount=delegation_cost,
                    task_description=step.description,
                    success=False
                )
        
        # 2. Resolve Tool
        tool_func = getattr(tool_registry, step.tool_name, None)
        if not tool_func:
            print(f"    [ERROR] Tool '{step.tool_name}' not found.")
            record = StepRecord(
                step_id=step.step_id,
                description=step.description,
                agent_id=step.agent_id,
                project_id=project_id,
                service_id=step.service_id,
                tool_name=step.tool_name,
                input=step.params,
                output=None,
                error=f"Tool '{step.tool_name}' not found",
                status="failed"
            )
            state.steps.append(record)
            state.current_step_index += 1
            continue

        # 3. Execute with Payment
        try:
            # The tool_func from PaidServiceTools handles the PaidToolWrapper logic internally
            result = tool_func(**step.params)
            
            # 4. Record Result
            error_msg = result.get("error")
            policy_action = "ALLOW"
            risk_level = result.get("_risk_level", "RISK_OK")
            
            if error_msg == "Policy Rejected":
                policy_action = "DENY"
                status = "denied"
            elif error_msg:
                status = "failed"
            else:
                status = "success"

            record = StepRecord(
                step_id=step.step_id,
                description=step.description,
                agent_id=step.agent_id,
                project_id=project_id,
                service_id=step.service_id,
                tool_name=step.tool_name,
                input=step.params,
                output=result,
                payment_id=result.get("_payment_id") or result.get("paymentId"),
                service_call_hash=result.get("_service_call_hash") or result.get("serviceCallHash"),
                tx_hash=result.get("_payment_tx") or result.get("txHash"),
                policy_action=result.get("policyAction", policy_action),
                risk_level=result.get("riskLevel", risk_level),
                error=error_msg,
                status=status,
                a2a_payment=a2a_payment_record
            )
            state.steps.append(record)
            
            if status == "denied":
                print(f"    [STOP] Step denied: {error_msg}")
                state.early_exit = True
                return state

        except Exception as e:
            print(f"    [ERROR] Execution exception: {e}")
            record = StepRecord(
                step_id=step.step_id,
                description=step.description,
                agent_id=step.agent_id,
                project_id=project_id,
                service_id=step.service_id,
                tool_name=step.tool_name,
                input=step.params,
                error=str(e),
                status="failed"
            )
            state.steps.append(record)
        
        state.current_step_index += 1

    return state
