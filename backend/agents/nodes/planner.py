import json
from typing import List
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.runnables import RunnableSequence

from ..state import GraphState, PlanStep, Plan
from ..utils import get_llm_instance

# Setup Parser
parser = PydanticOutputParser(pydantic_object=Plan)

PLANNER_SYSTEM = """
You are the **CEO & Planner** of an autonomous AI Startup.
Your job is to delegate the user's goal to your specialized employee agents.

**Your Employee Roster (Agents):**
1. **`startup-designer`**:
   - Role: Creative Director
   - Tools: `image_gen` (1.0 MNEE)
   - Use for: Making images, logos, artwork.

2. **`startup-analyst`**:
   - Role: Financial Analyst
   - Tools: `price_oracle` (0.05 MNEE), `batch_compute` (3.0 MNEE)
   - Use for: Checking crypto prices, market data, heavy calculations.

3. **`startup-archivist`**:
   - Role: Record Keeper
   - Tools: `log_archive` (0.01 MNEE)
   - Use for: Saving logs, storing records.

4. **`user-agent`**:
   - Role: General purpose / Fallback
   - Tools: All tools (but prefer specialists when possible).

**Instructions:**
- Break the User Goal into specific steps.
- **ASSIGN THE CORRECT `agent_id`** for each step based on the roles above.
- Set `max_mnee_cost` appropriately.
- Output ONLY JSON matching the `Plan` schema.

"""

PLANNER_HUMAN = """
**User Goal:**
"{goal}"

**Context:**
{context}

{format_instructions}
"""

def build_planner_chain(llm):
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", PLANNER_SYSTEM),
            ("human", PLANNER_HUMAN),
        ]
    ).partial(format_instructions=parser.get_format_instructions())

    chain = prompt | llm | parser
    return chain

def _keyword_plan(state: GraphState) -> List[PlanStep]:
    """Fallback keyword-based planning with Team Roles"""
    goal_lower = state.goal.lower()
    steps = []

    # Pattern 1: Image Generation -> Designer
    if any(word in goal_lower for word in ['image', 'generate', 'picture', 'avatar', 'logo']):
        steps.append(PlanStep(
            step_id="step_1_design",
            description="Generate requested artwork",
            agent_id="startup-designer",  # ASSIGN TO DESIGNER
            service_id="IMAGE_GEN_PREMIUM",
            tool_name="image_gen",
            estimated_quantity=1,
            max_mnee_cost=1.0,
            params={"prompt": state.goal}
        ))

    # Pattern 2: Price/Finance -> Analyst
    elif any(word in goal_lower for word in ['price', 'eth', 'mnee', 'cost', 'value']):
        symbol = "ETH"
        if "btc" in goal_lower: symbol = "BTC"
        
        steps.append(PlanStep(
            step_id="step_1_analysis",
            description=f"Check {symbol} price",
            agent_id="startup-analyst", # ASSIGN TO ANALYST
            service_id="PRICE_ORACLE",
            tool_name="price_oracle",
            estimated_quantity=1,
            max_mnee_cost=0.05,
            params={"symbol": symbol}
        ))

    # Default Fallback
    else:
        steps.append(PlanStep(
            step_id="step_1_fallback",
            description="Process user request",
            agent_id="user-agent",
            service_id=None,
            tool_name="respond",
            estimated_quantity=1,
            max_mnee_cost=0.0,
            params={"message": f"I understand: {state.goal}"}
        ))

    return steps

def planner_node(state: GraphState) -> GraphState:
    """
    Planner node: Converts user goal into structured execution plan with Team Delegation.
    """
    print(f"\n[PLANNER_NODE] CEO Planning for goal: {state.goal[:60]}...")

    # Use central utility for LLM
    llm = get_llm_instance()
    
    if not llm:
        print("[PLANNER_NODE] No LLM available, using simple fallback.")
        state.plan = _keyword_plan(state)
        return state

    planner_chain = build_planner_chain(llm)

    context = {
        "previous_steps": [s.model_dump() for s in state.steps],
        "active_agent": state.active_agent
    }

    try:
        plan_result: Plan = planner_chain.invoke({
            "goal": state.goal,
            "context": str(context),
        })
        
        state.plan = plan_result.steps
        state.current_step_index = 0
        
        print(f"[PLANNER_NODE] CEO Delegated {len(state.plan)} steps:")
        for i, step in enumerate(state.plan):
            print(f"  {i+1}. [{step.agent_id}] {step.description} (Tool: {step.tool_name})")
            
    except Exception as e:
        print(f"[PLANNER_NODE] CEO Planning failed: {e}, using fallback")
        state.plan = _keyword_plan(state)

    return state