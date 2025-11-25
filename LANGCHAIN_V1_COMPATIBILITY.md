# LangChain 1.0 Compatibility Guide

## Overview

This project has been updated to be compatible with LangChain 1.0 and LangGraph 0.2+. This document outlines the changes and compatibility considerations.

## Package Versions

### Updated requirements.txt

```txt
langchain>=1.0.0
langchain-openai>=0.3.0
langchain-aws>=0.3.0
langchain-core>=0.3.0
langgraph>=0.2.0
```

### Installation

```bash
# Upgrade to LangChain 1.0
pip install -U langchain langchain-openai langchain-aws langchain-core langgraph

# Or using uv
uv add langchain langchain-openai langchain-aws langchain-core langgraph
```

## Key Changes in LangChain 1.0

### 1. Import Changes

**LangChain 1.0 introduces cleaner top-level imports:**

```python
# New unified imports (LangChain 1.0)
from langchain.agents import create_agent
from langchain.messages import AIMessage, HumanMessage
from langchain.tools import tool
from langchain.chat_models import init_chat_model
from langchain.embeddings import init_embeddings
```

**LangGraph imports remain stable:**

```python
# LangGraph (no changes needed)
from langgraph.graph import StateGraph, END, START
from langgraph.checkpoint.memory import InMemorySaver
```

**Provider-specific imports (unchanged):**

```python
# Provider imports still work
from langchain_aws import ChatBedrockConverse
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
```

### 2. New `create_agent` Standard (Recommended)

LangChain 1.0 introduces `create_agent` as the standard way to build agents:

```python
from langchain.agents import create_agent

agent = create_agent(
    model="claude-sonnet-4-5-20250929",
    tools=[search_web, analyze_data, send_email],
    system_prompt="You are a helpful research assistant."
)

result = agent.invoke({
    "messages": [
        {"role": "user", "content": "Research AI safety trends"}
    ]
})
```

**Benefits:**
- Simpler API
- Built-in middleware support
- Unified content blocks
- Better structured output handling

### 3. StateGraph API (Unchanged)

**Good news:** Our existing StateGraph-based architecture is fully compatible with LangChain 1.0!

```python
# This code works in both old and new versions
from langgraph.graph import StateGraph, END, START

workflow = StateGraph(State)
workflow.add_node("planner", planner_node)
workflow.add_node("guardian", guardian_node)
workflow.add_node("executor", executor_node)
workflow.add_edge(START, "planner")
workflow.add_edge("planner", "guardian")
# ... etc
graph = workflow.compile()
```

## Compatibility Status

### ✅ Fully Compatible (No Changes Needed)

1. **LangGraph StateGraph**
   - `StateGraph`, `add_node()`, `add_edge()`, `compile()`
   - All work exactly as before

2. **Graph State Management**
   - `GraphState`, `StepRecord`, `PlanStep`
   - Pydantic models work unchanged

3. **LLM Initialization**
   - `ChatBedrockConverse`, `ChatOpenAI`
   - Provider imports unchanged

4. **Message Types**
   - `HumanMessage`, `AIMessage`
   - Work with both `langchain_core.messages` and unified imports

### ⚠️ Optional Improvements

These are NOT required but recommended for new code:

1. **Agent Creation**
   - Old: Custom LangGraph workflows (what we use)
   - New: `create_agent()` standard
   - **Status:** Our custom graph is more powerful, keep it

2. **Unified Content Blocks**
   - New feature in 1.0 for cross-provider compatibility
   - **Status:** Can add later if needed

3. **Middleware System**
   - New feature for PII detection, summarization, human-in-loop
   - **Status:** Guardian node provides similar functionality

## Our Project Status

### Current Architecture Compatibility

| Component | LangChain 1.0 Status | Notes |
|-----------|---------------------|-------|
| `backend/agents/graph.py` | ✅ Compatible | Uses StateGraph (stable API) |
| `backend/agents/nodes/planner.py` | ✅ Compatible | Uses provider imports |
| `backend/agents/nodes/guardian.py` | ✅ Compatible | Pure Python logic |
| `backend/agents/nodes/executor.py` | ✅ Compatible | No LangChain dependencies |
| `backend/agents/nodes/feedback.py` | ✅ Compatible | Pure Python logic |
| `backend/agents/nodes/summarizer.py` | ✅ Compatible | Pure Python logic |
| `backend/agents/state.py` | ✅ Compatible | Pydantic models |

### What We Changed

**Only one line needed updating:**

```python
# Added START constant for clearer entry point declaration
from langgraph.graph import StateGraph, END, START
```

That's it! Our architecture was already forward-compatible.

## Migration Guide (If Using Old LangChain Code)

### For Legacy Chains/Retrievers

If you have old code using deprecated chains:

```bash
# Install legacy package
pip install langchain-classic
```

```python
# Update imports
from langchain import ...  # Old
from langchain_classic import ...  # New

from langchain.chains import ...  # Old
from langchain_classic.chains import ...  # New
```

**Our project doesn't use these**, so no migration needed.

## Testing Compatibility

### 1. Install Updated Packages

```bash
cd backend
pip install -r requirements.txt
```

### 2. Run Tests

```bash
# Test new graph architecture
python test_graph.py

# Start backend
uvicorn app.main_graph:app --reload --port 8000

# Test API
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"agent_id":"user-agent","message":"What is ETH price?"}'
```

### 3. Verify Imports

```python
# Test in Python REPL
python3

>>> from langgraph.graph import StateGraph, END, START
>>> print("LangGraph import: OK")

>>> from langchain_aws import ChatBedrockConverse
>>> print("AWS import: OK")

>>> from langchain_openai import ChatOpenAI
>>> print("OpenAI import: OK")
```

## Benefits of LangChain 1.0

### 1. Simplified Namespace

**Before (multiple import paths):**
```python
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage
from langchain.agents import AgentExecutor
```

**After (unified imports):**
```python
from langchain.chat_models import init_chat_model
from langchain.messages import HumanMessage
from langchain.agents import create_agent
```

### 2. Better Type Safety

LangChain 1.0 improves TypeScript-style typing:
- Pydantic v2 throughout
- Better IDE autocomplete
- Clearer error messages

### 3. Production-Ready Defaults

- More stable APIs
- Better error handling
- Improved streaming support

## Future Considerations

### When to Use `create_agent`

If we ever need simpler agent creation:

```python
from langchain.agents import create_agent

# Simple agent (alternative to our StateGraph)
agent = create_agent(
    model="claude-sonnet-4-5-20250929",
    tools=[image_gen, price_oracle, batch_compute],
    system_prompt="You are a payment orchestration assistant."
)
```

**Why we don't use it now:**
- Our StateGraph gives more control (Guardian, Planner, Executor separation)
- We need custom payment enforcement logic
- Multi-step workflows with conditional routing

**When it might make sense:**
- Simple tool-calling agents without payment logic
- Prototyping new features quickly
- Internal admin tools

### Middleware Integration

LangChain 1.0 middleware could complement our Guardian:

```python
from langchain.agents.middleware import (
    PIIMiddleware,
    SummarizationMiddleware,
    HumanInTheLoopMiddleware
)

agent = create_agent(
    model="claude-sonnet-4-5-20250929",
    tools=[...],
    middleware=[
        PIIMiddleware("email", strategy="redact"),
        HumanInTheLoopMiddleware(interrupt_on={"send_payment": ...})
    ]
)
```

**Status:** Interesting for future, but Guardian handles this now.

## Troubleshooting

### Issue: Import Errors

```
ImportError: cannot import name 'START' from 'langgraph.graph'
```

**Solution:**
```bash
pip install -U langgraph>=0.2.0
```

### Issue: StateGraph Not Found

```
AttributeError: module 'langgraph.graph' has no attribute 'StateGraph'
```

**Solution:**
```bash
pip uninstall langgraph
pip install langgraph>=0.2.0
```

### Issue: Version Conflicts

```
ERROR: pip's dependency resolver does not currently take into account...
```

**Solution:**
```bash
# Clean install
pip uninstall langchain langchain-core langchain-openai langchain-aws langgraph
pip install langchain>=1.0.0 langchain-openai>=0.3.0 langchain-aws>=0.3.0 langgraph>=0.2.0
```

## Resources

### Official Documentation

- [LangChain 1.0 Release Notes](https://docs.langchain.com/oss/python/releases/langchain-v1/)
- [LangGraph Documentation](https://docs.langchain.com/langgraph/)
- [Migration Guide](https://docs.langchain.com/oss/python/releases/langchain-v1/#migration)

### Our Documentation

- `GRAPH_ARCHITECTURE.md` - Complete architecture guide
- `REFACTOR_SUMMARY.md` - Implementation details
- `backend/agents/graph.py` - Graph implementation
- `backend/test_graph.py` - Test examples

## Summary

**TL;DR:**
- ✅ Our codebase is LangChain 1.0 compatible out of the box
- ✅ Only needed to add `START` import for clarity
- ✅ StateGraph API is stable (no breaking changes)
- ✅ All tests pass with updated packages
- 📚 `create_agent` is available but not needed for our architecture

**Recommendation:** Update to LangChain 1.0 for better stability and future-proofing, but our existing code works perfectly without major changes.
