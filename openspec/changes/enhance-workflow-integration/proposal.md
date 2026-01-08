# Proposal: Enhance Workflow Integration

## Summary

Upgrade the workflow orchestration system from simulated execution to real integration with Escrow, A2A payments, and Policy Engine. Add intelligent agent auto-selection based on capabilities and reputation.

## Why

The current workflow implementation uses simulated execution for demo purposes. To win the hackathon, we need to demonstrate **real** MNEE payment flows:

1. **Judges expect real integration** - Simulated payments won't impress
2. **Freelancer Platform story** - Agents should automatically find the best worker for each task
3. **Differentiator** - Most competitors won't have multi-agent coordination with real payments

## What Changes

### 1. Real Escrow Integration
- Create actual escrow records for each workflow step
- Lock MNEE before step execution
- Release/refund based on verification results

### 2. Real A2A Payments
- Execute agent-to-agent transfers between steps
- Record transaction hashes on-chain
- Update agent balances in real-time

### 3. Policy Validation
- Check total workflow cost against customer budget BEFORE starting
- Validate each step against per-call limits
- Return clear error messages if budget insufficient

### 4. Agent Auto-Selection
- When workflow step specifies a `capability` instead of fixed `agent_id`
- Query AgentRegistry for agents with matching capability
- Select best agent based on: availability, reputation, cost
- Allow fallback to specific agent if preferred

## Impact

### Demo Story Enhancement
```
Before: "We simulate agent collaboration"
After:  "Watch real MNEE flow through multi-agent workflow with escrow protection"
```

### Affected Components
- `backend/workflow/executor.py` - Full rewrite for real execution
- `backend/workflow/engine.py` - Add auto-selection support
- `backend/agents/registry.py` - Add selection API
- `frontend/components/WorkflowView.tsx` - Show real tx hashes

## Success Criteria

1. Starting a workflow creates real escrow records (visible in Escrow Manager tab)
2. A2A transfers appear in A2A Network tab with tx hashes
3. Agent budgets decrease as workflow progresses
4. Policy denials prevent workflow start if budget insufficient
5. Auto-selection picks appropriate agent when capability specified
