# LangGraph Architecture - Core Agent Refactor

## Overview

This document describes the refactored Agent architecture that transforms the Omni-Agent from a "black box LLM + tools" into a **structured, auditable, and enterprise-grade payment orchestration system**.

## Architecture Principles

### 1. Structured State Flow

**Before:** Agent state was a mix of conversation history, temporary variables, and implicit state.

**After:** All state flows through `GraphState` - a single Pydantic model containing:
- User goal and conversation history
- Structured execution plan (`PlanStep[]`)
- Complete execution records (`StepRecord[]`)
- Payment metadata (tx_hash, service_call_hash, amount)
- Policy decisions (ALLOW/DENY/DOWNGRADE)
- Risk assessments (RISK_OK/RISK_REVIEW/RISK_BLOCK)

### 2. Clear Separation of Concerns

**Node Responsibilities:**

```
Planner     -> "Think": Convert user goal into structured PlanStep[]
Guardian    -> "Guard": Pre-flight risk assessment before payment
Executor    -> "Act": Execute tools with unified payment enforcement
Feedback    -> "Explain": User-friendly messages for denials
Summarizer  -> "Report": Generate final response with full audit trail
```

### 3. Single Payment Enforcement Point

**Before:** Multiple code paths could potentially bypass payment checks.

**After:** ALL tool calls go through:
```
Executor -> PaidToolWrapper -> PolicyEngine + PaymentClient + Guardian
```

No code outside Executor can execute paid tools.

### 4. Full Audit Trail

Every action produces a `StepRecord` containing:
- What was requested (input_params, service_id, tool_name)
- Who requested it (agent_id)
- Policy decision (policy_action, risk_level)
- Payment proof (payment_id, tx_hash, service_call_hash)
- Result (output, error, status)

## Graph Flow

```
                                  START
                                    |
                                    v
                              [ Planner ]
                                    |
                    Produces PlanStep[] with cost estimates
                                    |
                                    v
                  +---->      [ Guardian ]
                  |                 |
                  |   Pre-flight risk check (burst, large call, etc)
                  |                 |
                  |       +---------+----------+
                  |       |                    |
                  |   APPROVED              BLOCKED
                  |       |                    |
                  |       v                    |
                  |  [ Executor ]              |
                  |       |                    |
                  |  Execute with payment      |
                  |       |                    |
                  +-------+                    |
                    (Loop for next step)       |
                                               |
                                    +----------+
                                    |
                                    v
                              [ Feedback ]
                                    |
                        Aggregate denials and suggestions
                                    |
                                    v
                              [ Summarizer ]
                                    |
                        Generate final user response
                                    |
                                    v
                                   END
```

## Key Data Structures

### GraphState

```python
class GraphState(BaseModel):
    task_id: str
    goal: str
    active_agent: str
    messages: List[Dict[str, str]]
    plan: List[Dict[str, Any]]           # PlanStep[]
    current_step_index: int
    steps: List[StepRecord]              # Execution history
    final_answer: Optional[str]
    guardian_block: bool
    early_exit: bool
    treasury_balance: Optional[float]
```

### PlanStep

```python
class PlanStep(BaseModel):
    step_id: str
    description: str
    agent_id: str
    service_id: Optional[str]
    tool_name: str
    estimated_quantity: int
    max_mnee_cost: float                 # Budget planning
    params: Dict[str, Any]
```

### StepRecord

```python
class StepRecord(BaseModel):
    step_id: str
    agent_id: str
    service_id: Optional[str]
    tool_name: Optional[str]
    input_params: Dict[str, Any]
    output: Optional[Dict[str, Any]]

    # Payment tracking
    payment_id: Optional[str]
    service_call_hash: Optional[str]
    tx_hash: Optional[str]
    amount_mnee: Optional[float]

    # Policy enforcement
    policy_action: Optional[Literal["ALLOW", "DENY", "DOWNGRADE"]]
    risk_level: Optional[Literal["RISK_OK", "RISK_REVIEW", "RISK_BLOCK"]]

    # Status
    status: Literal["pending", "executing", "success", "failed", "denied"]
    error: Optional[str]
```

## Node Implementation Details

### Planner Node

**Location:** `backend/agents/nodes/planner.py`

**Responsibilities:**
1. Parse user goal and conversation history
2. Determine which services/tools are needed
3. Generate structured `PlanStep[]` (NOT free-form text)
4. Estimate costs for budget planning

**LLM Prompt Strategy:**
```python
system_prompt = """You are a task planner for MNEE Nexus.
You MUST respond with ONLY a JSON array of steps.

Each step must have:
{
    "step_id": "unique_id",
    "description": "what this step does",
    "agent_id": "user-agent",
    "service_id": "SERVICE_ID or null",
    "tool_name": "tool_function_name",
    "estimated_quantity": 1,
    "max_mnee_cost": 0.0,
    "params": {}
}
"""
```

**Fallback:** If LLM unavailable, uses keyword-based planning.

### Guardian Node

**Location:** `backend/agents/nodes/guardian.py`

**Responsibilities:**
1. Pre-flight risk assessment BEFORE payment
2. Detect burst attacks (>5 calls/minute with high cost)
3. Flag first-time large calls from low-priority agents
4. Track provider failure rates
5. Emergency circuit breaker

**Risk Levels:**
- `RISK_OK`: Normal operation
- `RISK_REVIEW`: Suspicious but allowed (for HIGH/MEDIUM priority)
- `RISK_BLOCK`: Hard block (burst, circuit breaker, etc.)

**Decision Logic:**
```python
if risk_level == "RISK_BLOCK":
    # Block immediately
    state.guardian_block = True

elif risk_level == "RISK_REVIEW":
    if agent_priority == "LOW":
        # Auto-block for low priority
        state.guardian_block = True
    else:
        # Allow with warning
        pass
```

### Executor Node

**Location:** `backend/agents/nodes/executor.py`

**Responsibilities:**
1. Get current `PlanStep` from state
2. Check if Guardian blocked it (skip if so)
3. Lookup tool function from registry
4. Call `PaidToolWrapper.wrap()` to enforce payment
5. Execute tool
6. Record result in `StepRecord`
7. Advance to next step

**Payment Enforcement:**
```python
# This is the ONLY path for paid service calls
wrapped_tool = paid_wrapper.wrap(
    tool_func=tool_func,
    service_id=step.service_id,
    agent_id=step.agent_id,
    cost_per_call=step.max_mnee_cost
)

result = wrapped_tool(
    payload_dict=step.params,
    quantity=step.estimated_quantity
)
```

**Tool Registry:**
All tools are registered centrally:
```python
register_tool("get_quote", _tool_get_quote)
register_tool("purchase_service", _tool_purchase_service)
register_tool("image_gen", _tool_image_gen)
register_tool("price_oracle", _tool_price_oracle)
register_tool("batch_compute", _tool_batch_compute)
register_tool("log_archive", _tool_log_archive)
register_tool("respond", _tool_respond)
```

### PolicyFeedback Node

**Location:** `backend/agents/nodes/feedback.py`

**Responsibilities:**
1. Scan steps for denied/failed operations
2. Aggregate reasons
3. Suggest alternatives (e.g., "Check budget", "Upgrade priority")
4. Add user-friendly messages to conversation

### Summarizer Node

**Location:** `backend/agents/nodes/summarizer.py`

**Responsibilities:**
1. Aggregate all step results
2. Format output based on tool type
3. Include payment information (tx_hash, amount)
4. Generate financial summary
5. Set `final_answer` for API response

## API Changes

### New Endpoint

**POST /chat** (main_graph.py version)

Request:
```json
{
  "agent_id": "user-agent",
  "message": "Generate a cyberpunk avatar",
  "task_id": "optional-task-id"
}
```

Response:
```json
{
  "response": "Image Generated...",
  "agent_id": "user-agent",
  "task_id": "abc-123",
  "steps": [
    {
      "step_id": "step_1",
      "agent_id": "user-agent",
      "service_id": "IMAGE_GEN_PREMIUM",
      "tool_name": "image_gen",
      "input_params": {"prompt": "..."},
      "output": {"imageUrl": "..."},
      "payment_id": "ticket-123",
      "tx_hash": "0x...",
      "service_call_hash": "0x...",
      "amount_mnee": 1.0,
      "policy_action": "ALLOW",
      "risk_level": "RISK_OK",
      "status": "success"
    }
  ],
  "success": true
}
```

### New Info Endpoint

**GET /graph/info**

Returns graph architecture details:
```json
{
  "architecture": "LangGraph StateGraph",
  "nodes": ["planner", "guardian", "executor", "feedback", "summarizer"],
  "flow": "planner -> guardian -> executor -> (loop) -> feedback -> summarizer -> END",
  "state_model": "GraphState with StepRecord[]",
  "payment_enforcement": "Unified in Executor node via PaidToolWrapper"
}
```

## Running the New Architecture

### 1. Start Services

```bash
# Start Hardhat fork
cd contracts
npx hardhat node

# Deploy contracts
npx hardhat run scripts/deploy.js --network localhost

# Start Guardian service
cd backend/guardian
./start_guardian.sh

# Start backend with new graph architecture
cd backend
uvicorn app.main_graph:app --reload --port 8000
```

### 2. Test the Graph

```bash
cd backend
python test_graph.py
```

This runs 4 tests:
1. Simple price query (should succeed)
2. Image generation (should succeed)
3. Budget limit check (should block ops-agent)
4. Multi-step A2A purchase (should succeed)

### 3. API Testing

```bash
# Simple request
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"agent_id":"user-agent","message":"What is ETH price?"}'

# Check graph info
curl http://localhost:8000/graph/info

# Check treasury status
curl http://localhost:8000/treasury
```

## Benefits of This Architecture

### 1. Engineering Benefits

- **Debuggable:** Every node's input/output is traceable via GraphState
- **Testable:** Each node can be unit tested independently
- **Maintainable:** Clear separation of concerns (plan vs guard vs execute)
- **Extensible:** Adding new services = register tool + add to Planner prompt

### 2. Security Benefits

- **Single enforcement point:** No way to bypass payment layer
- **Pre-flight checks:** Guardian blocks risky operations before money moves
- **Complete audit trail:** Every StepRecord has full payment metadata
- **Anti-spoofing:** service_call_hash binds payment to execution

### 3. Business Benefits

- **Transparent costs:** User sees exact cost breakdown per step
- **Policy compliance:** Every decision (ALLOW/DENY/DOWNGRADE) is logged
- **Budget control:** Real-time spending tracking per agent
- **Risk management:** Burst detection, circuit breaker, provider health checks

## Migration from Old Architecture

Old code is preserved in `backend/agents/omni_agent.py` and `backend/app/main.py`.

To switch:
1. **Keep old API running:** `uvicorn app.main:app --port 8000`
2. **Test new API:** `uvicorn app.main_graph:app --port 8001`
3. **Compare results:** Run same requests against both
4. **Switch over:** Update startup scripts to use `main_graph.py`

## Next Steps (P1 Priority)

1. **A2A Protocol Node:** Implement customer-agent <-> merchant-agent flow
2. **Guardian Circuit Breaker UI:** Admin panel to open/close circuit
3. **Step Timeline Frontend:** Visualize StepRecord[] in real-time
4. **Unit Tests:** Planner, Executor, Guardian node tests
5. **Integration Tests:** Full graph flow with mocked services

## Next Steps (P2 Priority)

6. **Planner LLM Fine-tuning:** Train on MNEE service catalog
7. **Guardian ML Model:** Replace rule-based risk with ML
8. **Multi-agent Coordination:** Parallel execution of independent steps
9. **Rollback Mechanism:** Undo payments if service delivery fails
10. **TEE Integration:** Migrate Guardian to Trusted Execution Environment
