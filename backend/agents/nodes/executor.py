from typing import Any, Dict, Callable
from ..state import GraphState, StepRecord, PlanStep

# We need a way to resolve tool_name to a function and wrapper.
# In a real app, these would be injected or imported from a registry.
# For now, we'll assume they are passed in or we import a registry.

def executor_node(state: GraphState, tool_registry: Any, policy_engine: Any) -> GraphState:
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

        # 1. Guardian Pre-check (Inline fallback)
        # (The main Guardian node ran before this, but we keep a sanity check or remove it)
        # Let's remove the hardcoded check since Guardian Node covers it intelligently now.
        # Or keep it as a "failsafe".
        
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
                status=status
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
