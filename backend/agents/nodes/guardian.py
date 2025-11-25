from typing import Optional, Any
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

from ..state import GraphState
from ..utils import get_llm_instance

# --- Data Model for Guardian Output ---
class GuardianDecision(BaseModel):
    risk_score: int = Field(..., description="Risk level from 0 (Safe) to 10 (Dangerous)")
    status: str = Field(..., description="Decision: 'APPROVE' or 'BLOCK'")
    reasoning: str = Field(..., description="Detailed audit explanation for the decision")

# --- Setup Parser ---
parser = PydanticOutputParser(pydantic_object=GuardianDecision)

GUARDIAN_SYSTEM = """
You are the **Chief Financial Officer (Guardian)** for an autonomous AI Agent system.
Your job is to AUDIT the execution plan proposed by the Planner Agent before any money (MNEE) is spent.

**Your Audit Criteria:**
1. **Relevance**: Do the planned tools/steps actually solve the User's Goal?
2. **Safety**: Are there any high-risk commands or excessive spending?
3. **Consistency**: Is the Agent hallucinating parameters? (e.g. inventing currency symbols)
4. **Pattern Analysis**: Look at the **Recent Transactions**. Is the agent spamming requests (Burst)? Is the spending pattern abnormal?
5. **Budget Compliance**: Check if the requested amount is within the Agent's remaining budget.

**Available Tools & Typical Costs:**
- image_gen: ~1.0 MNEE (Generates images)
- price_oracle: ~0.05 MNEE (Checks prices)
- batch_compute: ~3.0 MNEE (Heavy calculation)
- log_archive: ~0.01 MNEE (Storage)

**Output Format:**
You MUST return a JSON object matching this schema:
{{
    "risk_score": (int 0-10),
    "status": "APPROVE" or "BLOCK",
    "reasoning": "Your concise audit log explaining the decision."
}}
"""

GUARDIAN_HUMAN = """
**User Goal:**
"{goal}"

**Active Agent:**
{active_agent}

**Budget Status:**
{budget_status}

**Proposed Plan:**
{plan_json}

**Recent Transactions (Last 10):**
{history_json}

**Audit Report:**
"""

def guardian_node(state: GraphState, logger: Any, policy_engine: Any) -> GraphState:
    """
    Guardian Node: AI-powered audit of the execution plan with historical context and budget awareness.
    Args:
        state: Current GraphState
        logger: SystemLogger instance to fetch transaction history
        policy_engine: PolicyEngine instance to fetch budget info
    """
    print(f"\n[GUARDIAN_NODE] Auditing plan with {len(state.plan)} steps...")

    # Use central utility for LLM
    llm = get_llm_instance()
    
    if not llm:
        print("[GUARDIAN_NODE] No LLM available. Skipping audit (Default: APPROVE).")
        state.guardian_reasoning = "Audit skipped (No LLM)."
        return state

    # Prepare Prompt
    prompt = ChatPromptTemplate.from_messages([
        ("system", GUARDIAN_SYSTEM),
        ("human", GUARDIAN_HUMAN),
    ])
    
    chain = prompt | llm | parser

    # Convert plan to simple JSON for the LLM
    plan_summary = [
        {
            "step": s.step_id,
            "tool": s.tool_name,
            "cost_limit": s.max_mnee_cost,
            "agent": s.agent_id,
            "desc": s.description,
            "params": s.params
        }
        for s in state.plan
    ]

    # Fetch recent transactions
    history = []
    if logger:
        try:
            raw_history = logger.get_recent_transactions(limit=10)
            for tx in raw_history:
                history.append(f"[{tx.get('timestamp')}] {tx.get('agent_id')} spent {tx.get('amount')} MNEE on {tx.get('service_id')} ({tx.get('status')})")
        except Exception as e:
            print(f"[GUARDIAN_NODE] Failed to fetch history: {e}")
            history = ["(History unavailable)"]
    
    history_str = "\n".join(history) if history else "(No recent transactions)"

    # Fetch Budget Status
    budget_status = "Unknown"
    if policy_engine:
        try:
            # We need to check budget for the agent(s) involved in the plan
            # For simplicity, let's check the first step's agent or active_agent
            target_agent = state.plan[0].agent_id if state.plan else state.active_agent
            
            # Access AgentPolicy and UsageSnapshot
            # PolicyEngine stores agents in self.agents (dict of AgentPolicy)
            # And usage in self.usage (dict of UsageSnapshot)
            agent_policy = policy_engine.agents.get(target_agent)
            agent_usage = policy_engine.usage.get(target_agent)
            
            if agent_policy:
                daily = agent_policy.daily_budget_mnee
                spent = agent_usage.spent_today_mnee if agent_usage else 0.0
                remaining = daily - spent
                budget_status = f"Agent '{target_agent}': Spent {spent:.2f}/{daily:.2f} MNEE (Remaining: {remaining:.2f})"
            else:
                budget_status = f"Agent '{target_agent}' not found in policy."
                
        except Exception as e:
            print(f"[GUARDIAN_NODE] Failed to fetch budget: {e}")
            budget_status = f"Error fetching budget: {str(e)}"

    try:
        decision: GuardianDecision = chain.invoke({
            "goal": state.goal,
            "active_agent": state.active_agent,
            "budget_status": budget_status,
            "plan_json": str(plan_summary),
            "history_json": history_str
        })

        # Update State
        state.guardian_risk_score = decision.risk_score
        state.guardian_reasoning = decision.reasoning
        
        print(f"[GUARDIAN_NODE] Risk Score: {decision.risk_score}/10")
        print(f"[GUARDIAN_NODE] Decision: {decision.status}")
        print(f"[GUARDIAN_NODE] Reasoning: {decision.reasoning}")

        if decision.status == "BLOCK" or decision.risk_score >= 8:
            state.guardian_block = True
            state.final_answer = f"🛡️ **Security Block**: {decision.reasoning}"
        else:
            state.guardian_block = False

    except Exception as e:
        print(f"[GUARDIAN_NODE] Audit failed: {e}")
        state.guardian_reasoning = f"Audit Error: {e}"
        state.guardian_block = False

    return state