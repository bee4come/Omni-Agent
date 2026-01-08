# Delta: Workflow Capability

## ADDED Requirements

### Requirement: Workflow Definition
The system MUST support defining workflow templates with sequential steps, where each step specifies an agent, role, capability, and estimated cost.

#### Scenario: Define content creation workflow
- **WHEN** a workflow template is defined with steps Writer -> Designer -> Reviewer
- **THEN** the system stores the template with step order, agent assignments, and cost estimates

#### Scenario: Calculate total workflow cost
- **WHEN** a workflow template has steps costing 2.0, 3.0, and 0.5 MNEE
- **THEN** the system reports total cost as 5.5 MNEE

### Requirement: Workflow Execution
The system MUST execute workflow steps sequentially, creating an escrow for each step, performing A2A payment, executing the agent, verifying output, and releasing escrow.

#### Scenario: Execute workflow step with escrow
- **WHEN** a workflow step begins execution
- **THEN** the system creates an escrow locking the step cost
- **THEN** executes A2A payment from customer to step agent
- **THEN** invokes the agent to perform work
- **THEN** verifies the output quality
- **THEN** releases escrow upon successful verification

#### Scenario: Pass output between steps
- **WHEN** step N completes successfully
- **THEN** the output of step N becomes the input for step N+1

#### Scenario: Handle step failure
- **WHEN** a workflow step fails verification
- **THEN** the escrow is refunded to the customer
- **THEN** the workflow status is set to failed

### Requirement: Workflow Templates API
The system MUST provide API endpoints to list available workflow templates and retrieve template details.

#### Scenario: List workflow templates
- **WHEN** client calls GET /workflows/templates
- **THEN** the system returns list of available templates with id, name, description, total cost

#### Scenario: Get template details
- **WHEN** client calls GET /workflows/templates/{id}
- **THEN** the system returns template with full step definitions

### Requirement: Workflow Instance Management
The system MUST track workflow instances with status, current step, and step results.

#### Scenario: Start workflow instance
- **WHEN** client calls POST /workflows/start with template_id and customer_agent
- **THEN** the system creates a new instance with status "running"
- **THEN** creates escrows for all steps upfront
- **THEN** begins executing the first step

#### Scenario: Query workflow status
- **WHEN** client calls GET /workflows/instances/{id}
- **THEN** the system returns instance with current_step_index, step statuses, escrow statuses

### Requirement: Workflow Visualization
The system MUST provide a frontend component displaying workflow progress as a horizontal pipeline with animated step transitions.

#### Scenario: Display workflow pipeline
- **WHEN** user views an active workflow
- **THEN** the UI shows steps as connected cards with role, agent, cost, and status
- **THEN** completed steps show green, running steps pulse blue, pending steps show gray

#### Scenario: Show real-time progress
- **WHEN** a workflow step status changes
- **THEN** the UI updates via WebSocket without page refresh
