# Swarm Architecture - Multi-Agent Coordination

## Overview

The Swarm architecture implements a multi-agent system for coordinating AI-driven commerce. It demonstrates the **A2A (Agent-to-Agent) Payment Flow** where specialized agents collaborate to fulfill user requests.

## Architecture

```
User Request
    |
    v
┌─────────────────────────────────────────────────────────┐
│              Swarm Orchestrator                         │
└─────────────────────────────────────────────────────────┘
    |
    |---> [Manager Agent]    (Plans and decomposes tasks)
    |
    |---> [Customer Agent]   (Executes purchases)
    |         |
    |         v
    |     [Guardian Service] (Signs payments)
    |         |
    |         v
    |     [Merchant Agent]   (Delivers services)
    |
    |---> [Treasurer Agent]  (Records transactions)
    |
    v
Complete Result
```

## Agents

### 1. Manager Agent

**Role:** Task planning and decomposition

**Responsibilities:**
- Analyze natural language requests
- Identify required services
- Create structured execution plans
- Estimate costs

**Example:**
```python
from agents.swarm import ManagerAgent

manager = ManagerAgent()
plan = manager.plan("Generate a cyberpunk avatar and check ETH price")

# Output: ExecutionPlan with 2 tasks:
# 1. IMAGE_GEN_PREMIUM (1.0 MNEE)
# 2. PRICE_ORACLE (0.05 MNEE)
```

### 2. Customer Agent

**Role:** Purchase execution

**Responsibilities:**
- Request quotes from merchants
- Execute payments via Payment Client (which calls Guardian)
- Retrieve delivered services
- Handle errors and retries

**Example:**
```python
from agents.swarm import CustomerAgent

customer = CustomerAgent(payment_client=payment_client)
result = customer.execute_task(task_plan, merchant_agent)

# Result includes:
# - payment_id
# - service_result
# - cost
```

### 3. Merchant Agent

**Role:** Service provider

**Responsibilities:**
- Provide quotes for services
- Verify payments (optionally on-chain)
- Deliver services after payment
- Track delivery metrics

**Example:**
```python
from agents.swarm import MerchantAgent

merchant = MerchantAgent(merchant_id="merchant-1")

# Step 1: Provide quote
quote = merchant.quote("IMAGE_GEN_PREMIUM", {"prompt": "cyberpunk"})

# Step 2: Fulfill after payment
result = merchant.fulfill(
    service_id="IMAGE_GEN_PREMIUM",
    task_id="task-123",
    payment_id="payment-abc",
    service_call_hash="0x...",
    payload={"prompt": "cyberpunk"}
)
```

### 4. Treasurer Agent

**Role:** Financial record keeper

**Responsibilities:**
- Record all transactions
- Generate financial reports
- Detect anomalies
- Provide audit trail

**Example:**
```python
from agents.swarm import TreasurerAgent

treasurer = TreasurerAgent()

# Record transaction
record = treasurer.record_transaction(receipt)

# Generate reports
daily_report = treasurer.get_daily_report()
agent_report = treasurer.get_agent_report("customer-agent")
anomalies = treasurer.detect_anomalies()
```

## Complete Flow Example

### Basic Usage

```python
from agents.swarm import SwarmOrchestrator
from payment.client import PaymentClient
from policy.engine import PolicyEngine

# Initialize components
policy_engine = PolicyEngine("config/agents.yaml", "config/services.yaml")
payment_client = PaymentClient(policy_engine=policy_engine)

# Create Swarm Orchestrator
swarm = SwarmOrchestrator(
    payment_client=payment_client,
    policy_engine=policy_engine
)

# Process user request
result = swarm.process_request(
    user_request="Generate a cyberpunk avatar for me",
    requesting_agent_id="user-agent"
)

# Check result
if result["success"]:
    for task_result in result["task_results"]:
        if task_result["success"]:
            print(f"Service: {task_result['service_id']}")
            print(f"Result: {task_result['service_data']}")
            print(f"Cost: {task_result['cost']} MNEE")
```

### Detailed Flow

```python
# Step 1: Manager plans
plan = swarm.manager.plan("Generate image and check price")
print(f"Plan: {len(plan.tasks)} tasks, {plan.total_estimated_cost} MNEE")

# Step 2: Customer executes
for task in plan.tasks:
    # Customer requests quote
    quote = swarm.merchant.quote(task.service_id, task.payload)

    # Customer pays (via Guardian)
    result = swarm.customer.execute_task(task, swarm.merchant)

    # Treasurer records
    if result.success:
        swarm.treasurer.record_transaction({
            "agent_id": "user-agent",
            "service_id": task.service_id,
            "payment_id": result.payment_id,
            "amount": result.cost,
            ...
        })
```

## Payment Flow Details

### Before Guardian (Insecure)

```
Customer Agent
    |
    v
Payment Client [PRIVATE KEY]  <-- Security Issue!
    |
    v
MNEE PaymentRouter
```

### With Guardian (Secure)

```
Customer Agent
    |
    v
Payment Client
    |
    v
Guardian Service [PRIVATE KEY]  <-- Isolated!
    |
    v
MNEE PaymentRouter
```

### A2A Commerce Flow

1. **Request Phase**
   - User makes request
   - Manager creates plan
   - Customer requests quotes from Merchants

2. **Payment Phase**
   - Customer initiates payment via Payment Client
   - Payment Client calls Guardian /quote (pre-check)
   - Guardian /pay executes on-chain payment
   - PaymentRouter transfers MNEE

3. **Delivery Phase**
   - Customer provides payment proof to Merchant
   - Merchant verifies payment (optionally on-chain)
   - Merchant delivers service

4. **Recording Phase**
   - Treasurer records transaction
   - Financial reports updated
   - Anomaly detection runs

## Configuration

### Services Configuration

Define available services in `config/services.yaml`:

```yaml
services:
  - id: "IMAGE_GEN_PREMIUM"
    unitPrice: 1.0
    providerAddress: "0x..."
    active: true

  - id: "PRICE_ORACLE"
    unitPrice: 0.05
    providerAddress: "0x..."
    active: true
```

### Agent Configuration

Define agent budgets in `config/agents.yaml`:

```yaml
agents:
  - id: "customer-agent"
    priority: "HIGH"
    dailyBudget: 100.0
    maxPerCall: 10.0
```

## Monitoring

### System Statistics

```python
stats = swarm.get_system_stats()

# Returns:
{
    "manager": {
        "total_plans": 10,
        "total_tasks": 25,
        "total_estimated_cost": 35.5
    },
    "customer": {
        "total_purchases": 25,
        "successful": 23,
        "failed": 2,
        "total_spent": 34.8
    },
    "merchant": {
        "quotes_issued": 25,
        "services_delivered": 23,
        "total_revenue": 34.8
    },
    "treasurer": {
        "total_transactions": 23,
        "total_volume": 34.8,
        "success_rate": 92.0
    }
}
```

### Agent Reports

```python
# Get report for specific agent
report = swarm.get_agent_report("customer-agent")

# Get report for specific service
report = swarm.get_service_report("IMAGE_GEN_PREMIUM")

# Detect anomalies
anomalies = swarm.detect_anomalies()
```

## Testing

### Unit Test Example

```python
def test_manager_planning():
    manager = ManagerAgent()
    plan = manager.plan("Generate an image")

    assert len(plan.tasks) > 0
    assert plan.tasks[0].service_id == "IMAGE_GEN_PREMIUM"
    assert plan.total_estimated_cost > 0
```

### Integration Test Example

```python
def test_complete_flow():
    # Setup
    swarm = SwarmOrchestrator(payment_client, policy_engine)

    # Execute
    result = swarm.process_request("Generate image")

    # Verify
    assert result["success"]
    assert result["execution_summary"]["successful_tasks"] > 0
    assert result["financial_summary"]["total_spent"] > 0
```

## Future Enhancements

### Short-term
- [ ] LLM integration for Manager (replace pattern matching)
- [ ] On-chain payment verification for Merchant
- [ ] Real-time anomaly alerts
- [ ] Multi-merchant quote comparison

### Long-term
- [ ] Reputation system for Merchants
- [ ] Dynamic pricing based on demand
- [ ] Cross-chain payments
- [ ] Decentralized Merchant registry

## Related Documentation

- **Guardian Service:** `backend/guardian/README.md`
- **Payment Client:** `backend/payment/client.py`
- **Policy Engine:** `backend/policy/engine.py`
- **Architecture:** `FINAL_PROJECT_OVERVIEW.md`
