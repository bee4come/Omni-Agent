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

**Available Tools and EXACT Parameters:**
- `image_gen`: params={{"prompt": "<description of image>"}}
- `price_oracle`: params={{"symbol": "ETH" or "BTC" or other crypto symbol}}
- `batch_compute`: params={{"payload": "<data to process>"}}
- `log_archive`: params={{"content": "<log content>"}}
- `respond`: params={{"message": "<response text>"}}

**Instructions:**
- Break the User Goal into specific steps.
- **ASSIGN THE CORRECT `agent_id`** for each step based on the roles above.
- **USE EXACT PARAMETER NAMES** as shown above. Do NOT invent new parameter names.
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
    if any(word in goal_lower for word in ['image', 'picture', 'avatar', 'logo', 'artwork', 'marketing image']):
        steps.append(PlanStep(
            step_id="step_1_design",
            description="Generate requested artwork",
            agent_id="startup-designer",
            service_id="IMAGE_GEN_PREMIUM",
            tool_name="image_gen",
            estimated_quantity=1,
            max_mnee_cost=1.0,
            params={"prompt": state.goal}
        ))

    # Pattern 2: Price/Market Analysis -> Analyst (price_oracle + batch_compute)
    elif any(word in goal_lower for word in ['price', 'pricing', 'competitor', 'market', 'analyze', 'analysis', 'report']):
        symbol = "ETH"
        if "btc" in goal_lower: symbol = "BTC"
        
        # Step 1: Get price data
        steps.append(PlanStep(
            step_id="step_1_data",
            description=f"Gather market pricing data",
            agent_id="startup-analyst",
            service_id="PRICE_ORACLE",
            tool_name="price_oracle",
            estimated_quantity=1,
            max_mnee_cost=0.1,
            params={"symbol": symbol}
        ))
        
        # Step 2: Process and analyze
        steps.append(PlanStep(
            step_id="step_2_analyze",
            description="Analyze data and generate report",
            agent_id="startup-analyst",
            service_id="BATCH_COMPUTE",
            tool_name="batch_compute",
            estimated_quantity=1,
            max_mnee_cost=3.0,
            params={"payload": f"analyze: {state.goal}"}
        ))

    # Pattern 3: Batch compute only
    elif any(word in goal_lower for word in ['batch', 'compute', 'process', 'ml', 'inference']):
        steps.append(PlanStep(
            step_id="step_1_compute",
            description="Process batch computation",
            agent_id="startup-analyst",
            service_id="BATCH_COMPUTE",
            tool_name="batch_compute",
            estimated_quantity=1,
            max_mnee_cost=3.0,
            params={"payload": state.goal}
        ))

    # Pattern 4: Archive/Log
    elif any(word in goal_lower for word in ['log', 'archive', 'save', 'record']):
        steps.append(PlanStep(
            step_id="step_1_archive",
            description="Archive the content",
            agent_id="startup-archivist",
            service_id="LOG_ARCHIVE",
            tool_name="log_archive",
            estimated_quantity=1,
            max_mnee_cost=0.01,
            params={"content": state.goal}
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