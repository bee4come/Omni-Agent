# Tasks: Add Agent Collaboration Workflow

## 1. Backend Core Models
- [x] 1.1 Create `backend/workflow/__init__.py`
- [x] 1.2 Create `backend/workflow/engine.py` with WorkflowStep, WorkflowDefinition, WorkflowInstance models
- [x] 1.3 Create `backend/workflow/templates.py` with CONTENT_CREATION and DATA_ANALYSIS templates

## 2. Backend Executor
- [x] 2.1 Create `backend/workflow/executor.py` with WorkflowExecutor class
- [x] 2.2 Implement `start_workflow()` - creates escrows, begins execution
- [x] 2.3 Implement `execute_step()` - A2A payment, agent call, verification
- [x] 2.4 Implement `get_instance_status()` - returns current state

## 3. Backend API
- [x] 3.1 Add `GET /workflows/templates` endpoint
- [x] 3.2 Add `GET /workflows/templates/{workflow_id}` endpoint
- [x] 3.3 Add `POST /workflows/start` endpoint
- [x] 3.4 Add `GET /workflows/instances` endpoint
- [x] 3.5 Add `GET /workflows/instances/{instance_id}` endpoint

## 4. Frontend Types and API
- [x] 4.1 Add workflow types to `frontend/lib/types.ts`
- [x] 4.2 Add workflow API functions to `frontend/lib/api.ts`

## 5. Frontend Components
- [x] 5.1 Create `frontend/components/WorkflowView.tsx` - pipeline visualization
- [x] 5.2 Create `frontend/components/WorkflowDemo.tsx` - demo control panel
- [x] 5.3 Add Workflow tab to `frontend/components/AppShell.tsx`

## 6. Integration and Polish
- [x] 6.1 Add WebSocket events for workflow progress (using polling fallback)
- [x] 6.2 Add Framer Motion animations for step transitions
- [x] 6.3 Test end-to-end workflow execution
- [x] 6.4 Verify frontend build passes

## 7. Documentation
- [x] 7.1 Update `docs/DEMO_SCRIPT.md` with workflow demo instructions

---

**Status: COMPLETE**

All tasks implemented. Ready for `openspec archive add-agent-workflow` when approved.
