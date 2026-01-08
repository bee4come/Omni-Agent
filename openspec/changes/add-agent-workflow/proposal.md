# Change: Add Agent Collaboration Workflow

## Why

MNEE Nexus currently supports single-agent execution and individual A2A payments, but lacks the ability to define multi-agent workflows where agents collaborate on complex tasks. This limits the demo appeal and fails to showcase the full potential of agent-to-agent commerce.

For the AI & Agent Payments hackathon track (12,500 MNEE prize), we need to demonstrate sophisticated agent coordination with visible payment flows between collaborating agents.

## What Changes

- **ADDED** Workflow Engine with templates (Content Creation, Data Analysis pipelines)
- **ADDED** Workflow Executor that chains escrow-lock -> execute -> verify -> release per step
- **ADDED** API endpoints: `/workflows/templates`, `/workflows/start`, `/workflows/instances`
- **ADDED** Frontend WorkflowView component with pipeline visualization
- **ADDED** Frontend WorkflowDemo panel for hackathon presentation
- **ADDED** Real-time workflow progress via WebSocket

## Impact

- Affected specs: `workflow` (new capability)
- Affected code:
  - `backend/workflow/` (new package)
  - `backend/app/main.py` (new endpoints)
  - `frontend/components/WorkflowView.tsx` (new)
  - `frontend/components/WorkflowDemo.tsx` (new)
  - `frontend/components/AppShell.tsx` (add tab)
  - `frontend/lib/api.ts` (add functions)
  - `frontend/lib/types.ts` (add types)

## Demo Story

A "Freelancer Platform" where:
1. Customer agent submits a task (e.g., "Create marketing report")
2. Writer agent researches and drafts content (2.0 MNEE)
3. Designer agent creates visuals (3.0 MNEE)
4. Reviewer agent validates and archives (0.5 MNEE)

Each step creates an escrow, executes A2A payment, and releases upon verification.
