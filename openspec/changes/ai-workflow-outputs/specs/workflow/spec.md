# Delta: AI-Generated Workflow Outputs

## ADDED Requirements

### Requirement: LLM-Generated Step Outputs
The system MUST generate realistic outputs using LLM for each workflow step.

#### Scenario: Writer Step Generation
- GIVEN a workflow step with role "Writer"
- WHEN the step executes
- THEN the system generates a 3-paragraph draft using LLM
- AND the output includes title, sections, and word count

#### Scenario: Reviewer Step Generation
- GIVEN a workflow step with role "Reviewer"
- WHEN the step executes
- THEN the system generates specific feedback using LLM
- AND the output includes score, approved status, and actionable comments

#### Scenario: LLM Failure Fallback
- GIVEN LLM API is unavailable
- WHEN generating step output
- THEN the system falls back to mock data
- AND logs warning about fallback

### Requirement: Agent Bid Visibility
The system MUST show competing agent bids before workflow starts.

#### Scenario: Display Agent Bids
- GIVEN a workflow is about to start
- WHEN agents are resolved for each step
- THEN the system returns bid details for all matching agents
- AND includes price, reputation, estimated_time for each

#### Scenario: Selection Reason
- GIVEN multiple agents can handle a capability
- WHEN best agent is selected
- THEN the selection_reason is recorded
- AND explains why this agent was chosen over others

### Requirement: Output Display
The system MUST display generated outputs in expandable visual cards.

#### Scenario: Expandable Output Card
- GIVEN a workflow step has completed
- WHEN user clicks the step card
- THEN output content is displayed in formatted card
- AND includes copy-to-clipboard for text content

#### Scenario: Role-Specific Rendering
- GIVEN step has role "Designer"
- WHEN displaying output
- THEN shows image previews and asset list
- AND uses appropriate visual styling for design content
