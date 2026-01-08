# Tasks: AI-Generated Workflow Outputs & Coordination Demo

## 1. Backend: LLM Output Generation
- [x] 1.1 Add `generate_step_output()` to WorkflowExecutor
- [x] 1.2 Create prompts for each role (Writer, Designer, Reviewer, Analyzer)
- [x] 1.3 Integrate with existing LLM wrapper (OmniAgent or direct API)
- [x] 1.4 Add output caching to avoid repeated API calls
- [x] 1.5 Graceful fallback to mock data if LLM fails

## 2. Backend: Coordination Data
- [x] 2.1 Add `get_agent_bids()` to AgentRegistry - return competing agents
- [x] 2.2 Include bid details: price, estimated_time, reputation, capability_match
- [x] 2.3 Add `selection_reason` to WorkflowStepStatus model
- [x] 2.4 Record why each agent was selected in step output

## 3. Frontend: Output Display Component
- [x] 3.1 Create `WorkflowOutputCard.tsx` - expandable output display
- [x] 3.2 Add role-specific renderers (WriterOutput, DesignerOutput, etc.)
- [x] 3.3 Add syntax highlighting for JSON/code content
- [x] 3.4 Add copy-to-clipboard functionality
- [x] 3.5 Integrate into WorkflowView expanded step details

## 4. Frontend: Agent Coordination Visualization
- [x] 4.1 Create `AgentBidding.tsx` - shows competing agents
- [x] 4.2 Add bid cards with price, time, reputation display
- [x] 4.3 Animate selection process (2-3 second visual)
- [x] 4.4 Show "winner" highlight with reason
- [x] 4.5 Integrate into WorkflowDemo before execution starts

## 5. Integration & Polish
- [x] 5.1 Update WorkflowDemo to show coordination phase
- [x] 5.2 Add loading states for LLM generation
- [x] 5.3 Test full flow with real LLM outputs
- [x] 5.4 Update DEMO_SCRIPT.md with new demo points
