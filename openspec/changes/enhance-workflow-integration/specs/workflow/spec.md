# Delta: Workflow Integration Enhancement

## MODIFIED Requirements

### Requirement: Workflow Budget Validation
The system MUST validate total workflow cost against customer budget before starting.

#### Scenario: Sufficient Budget
- GIVEN customer agent has 20 MNEE remaining budget
- WHEN starting a workflow costing 5.5 MNEE total
- THEN workflow starts successfully

#### Scenario: Insufficient Budget
- GIVEN customer agent has 3 MNEE remaining budget
- WHEN starting a workflow costing 5.5 MNEE total
- THEN workflow is rejected with error "Insufficient budget: need 5.5, have 3.0"

### Requirement: Real Escrow Creation
The system MUST create actual escrow records for each workflow step.

#### Scenario: Escrow Per Step
- GIVEN a 3-step workflow is started
- WHEN workflow execution begins
- THEN 3 escrow records are created with status "locked"
- AND each escrow contains correct payer, payee, and amount

#### Scenario: Escrow Release on Success
- GIVEN a workflow step completes successfully
- WHEN verification passes
- THEN corresponding escrow status changes to "released"
- AND funds are transferred to merchant agent

### Requirement: Real A2A Payments
The system MUST execute actual A2A transfers between agents during workflow.

#### Scenario: Payment Execution
- GIVEN workflow step with customer "user-agent" and merchant "startup-designer"
- WHEN step execution begins
- THEN A2A payment is executed from user-agent to startup-designer
- AND transaction hash is recorded in step status

## ADDED Requirements

### Requirement: Agent Auto-Selection
The system MUST automatically select the best agent when step specifies capability instead of agent_id.

#### Scenario: Capability-Based Selection
- GIVEN workflow step requires capability "image_gen"
- AND agents "designer-a" (reputation 0.9) and "designer-b" (reputation 0.7) have this capability
- WHEN workflow starts
- THEN "designer-a" is selected for the step (highest reputation)

#### Scenario: No Available Agent
- GIVEN workflow step requires capability "quantum_compute"
- AND no registered agents have this capability
- WHEN workflow starts
- THEN workflow fails with error "No agent available for capability: quantum_compute"

### Requirement: Workflow Progress Events
The system MUST emit events for workflow progress updates.

#### Scenario: Step Completion Event
- GIVEN workflow is running
- WHEN a step completes
- THEN event is emitted with step_id, status, cost, and tx_hash
