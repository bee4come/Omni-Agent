# MNEE Nexus SDK

Easy-to-use SDK for integrating MNEE-based payments into AI agent systems.

## Quick Start

### Installation

```bash
# Add SDK to Python path
export PYTHONPATH="${PYTHONPATH}:/path/to/Omni-Agent"

# Or install dependencies
cd Omni-Agent
pip install -r backend/requirements.txt
```

### Basic Usage

```python
from sdk import MNEEAgent

# Initialize agent
agent = MNEEAgent(agent_id="my-agent")

# Request service with natural language
result = agent.request_service("Generate a cyberpunk avatar")

# Check result
if result["success"]:
    print(f"Cost: {result['total_cost']} MNEE")
    for data in result["service_data"]:
        print(f"Result: {data}")
```

## SDK Components

### 1. MNEEAgent - High-Level Interface

The simplest way to use MNEE services.

```python
from sdk import MNEEAgent

agent = MNEEAgent(
    agent_id="my-agent",
    config_path="config/agents.yaml",  # Optional
    use_swarm=True  # Use multi-agent coordination
)

# Request service
result = agent.request_service("Generate an image and check ETH price")

# Get budget status
budget = agent.get_budget_status()
print(f"Remaining budget: {budget['remaining_budget']} MNEE")

# List available services
services = agent.list_available_services()
for service in services:
    print(f"{service['id']}: {service['unit_price']} MNEE")

# Get transaction history
history = agent.get_transaction_history()
print(f"Total transactions: {len(history)}")
```

### 2. PaymentSDK - Direct Payment Control

For fine-grained payment control.

```python
from sdk import PaymentSDK

sdk = PaymentSDK(agent_id="my-agent")

# Check policy before paying
decision = sdk.check_policy("IMAGE_GEN_PREMIUM", estimated_cost=1.0)
if decision["action"] == "ALLOW":
    # Execute payment
    result = sdk.pay_for_service(
        service_id="IMAGE_GEN_PREMIUM",
        quantity=1,
        payload={"prompt": "cyberpunk avatar", "style": "neon"}
    )

    if result.success:
        print(f"Payment ID: {result.payment_id}")
        print(f"Transaction: {result.tx_hash}")
        print(f"Cost: {result.amount} MNEE")
    else:
        print(f"Payment failed: {result.error}")

# Get service price
price = sdk.get_service_price("IMAGE_GEN_PREMIUM")
print(f"Price: {price} MNEE")

# Check budget
budget = sdk.get_agent_budget()
print(f"Daily budget: {budget['daily_budget']}")
print(f"Current spending: {budget['current_spending']}")
print(f"Remaining: {budget['remaining']} MNEE")
```

### 3. SwarmSDK - Multi-Agent Orchestration

For complex multi-agent workflows.

```python
from sdk import SwarmSDK

swarm = SwarmSDK()

# Execute complex request
result = swarm.execute(
    user_request="Generate 3 images and analyze pricing data",
    agent_id="my-agent"
)

# Check results
print(f"Success: {result['success']}")
print(f"Total cost: {result['total_cost']} MNEE")
print(f"Tasks completed: {result['successful_tasks']}/{result['total_tasks']}")

# Inspect individual tasks
for task in result["tasks"]:
    if task["success"]:
        print(f"\nService: {task['service_id']}")
        print(f"Payment ID: {task['payment_id']}")
        print(f"Result: {task['data']}")

# Get system statistics
stats = swarm.get_statistics()
print(f"\nManager: {stats['manager']['total_plans']} plans created")
print(f"Customer: {stats['customer']['total_purchases']} purchases")
print(f"Merchant: {stats['merchant']['services_delivered']} services delivered")
print(f"Treasurer: {stats['treasurer']['total_volume']} MNEE processed")

# Get daily summary
summary = swarm.get_daily_summary()
print(f"\nDaily Summary:")
print(f"  Transactions: {summary['total_transactions']}")
print(f"  Volume: {summary['total_volume']} MNEE")
print(f"  Success Rate: {summary['success_rate']}%")

# Detect anomalies
anomalies = swarm.detect_anomalies()
if anomalies["anomalies_detected"] > 0:
    print(f"\nWarning: {anomalies['anomalies_detected']} anomalies detected!")
    for anomaly in anomalies["anomalies"]:
        print(f"  - {anomaly['type']}: {anomaly['severity']}")
```

## Configuration

### Agent Configuration (agents.yaml)

Define agent budgets and priorities:

```yaml
agents:
  - id: "my-agent"
    priority: "HIGH"        # HIGH, MEDIUM, LOW
    dailyBudget: 100.0      # Daily spending limit in MNEE
    maxPerCall: 10.0        # Maximum per transaction
```

### Service Configuration (services.yaml)

Define available services:

```yaml
services:
  - id: "IMAGE_GEN_PREMIUM"
    unitPrice: 1.0          # Cost per unit in MNEE
    providerAddress: "0x..."
    active: true

  - id: "PRICE_ORACLE"
    unitPrice: 0.05
    providerAddress: "0x..."
    active: true
```

## Architecture

The SDK provides three levels of abstraction:

### Level 1: MNEEAgent (Recommended)
- Simplest interface
- Natural language requests
- Automatic multi-agent coordination
- Best for most use cases

### Level 2: PaymentSDK
- Direct payment control
- Policy checking
- Budget management
- Best for custom workflows

### Level 3: SwarmSDK
- Full multi-agent orchestration
- Advanced reporting
- Anomaly detection
- Best for complex systems

## Security

### Guardian Service

All payments are processed through Guardian Service:

```
Your Code
    |
    v
SDK (PaymentSDK/MNEEAgent)
    |
    v
Payment Client
    |
    v
Guardian Service [PRIVATE KEY]
    |
    v
MNEE Smart Contract
```

**Key Security Features:**
- Private keys never exposed to your code
- Guardian Service is isolated
- All payments audited
- Policy enforcement before payments

## Examples

### Example 1: Simple Image Generation

```python
from sdk import MNEEAgent

agent = MNEEAgent(agent_id="my-app")
result = agent.request_service("Generate a logo for my startup")

if result["success"]:
    image_url = result["service_data"][0]["image_url"]
    print(f"Image generated: {image_url}")
    print(f"Cost: {result['total_cost']} MNEE")
```

### Example 2: Batch Processing

```python
from sdk import PaymentSDK

sdk = PaymentSDK(agent_id="batch-processor")

# Check budget first
budget = sdk.get_agent_budget()
if budget["remaining"] < 10.0:
    print("Insufficient budget!")
    exit(1)

# Process multiple items
for item in items:
    result = sdk.pay_for_service(
        service_id="BATCH_COMPUTE",
        payload={"data": item}
    )
    if result.success:
        print(f"Processed {item}: {result.payment_id}")
```

### Example 3: Multi-Service Workflow

```python
from sdk import SwarmSDK

swarm = SwarmSDK()

# Complex workflow
result = swarm.execute(
    """
    1. Generate a product image
    2. Get current market prices
    3. Run batch analysis on competitors
    4. Archive results
    """,
    agent_id="marketing-agent"
)

# Process results
for task in result["tasks"]:
    if task["success"]:
        print(f"{task['service_id']}: {task['data']}")

print(f"\nTotal cost: {result['total_cost']} MNEE")
```

### Example 4: Budget Monitoring

```python
from sdk import MNEEAgent

agent = MNEEAgent(agent_id="monitored-agent")

# Check budget before operation
budget = agent.get_budget_status()
print(f"Budget: {budget['remaining_budget']}/{budget['daily_budget']} MNEE")

if budget["remaining_budget"] < 5.0:
    print("Warning: Low budget!")

# Execute operation
result = agent.request_service("Generate image")

# Check updated budget
updated_budget = agent.get_budget_status()
print(f"Spent: {budget['current_spending'] - updated_budget['current_spending']} MNEE")
```

## Error Handling

```python
from sdk import MNEEAgent

agent = MNEEAgent(agent_id="my-agent")

try:
    result = agent.request_service("Generate image")

    if not result["success"]:
        print(f"Request failed: {result.get('error', 'Unknown error')}")
    else:
        # Process successful result
        pass

except Exception as e:
    print(f"SDK error: {e}")
```

## Best Practices

### 1. Always Check Budget

```python
budget = agent.get_budget_status()
if budget["remaining_budget"] < estimated_cost:
    # Handle insufficient budget
    pass
```

### 2. Handle Failures Gracefully

```python
result = agent.request_service(request)
if not result["success"]:
    # Log failure, retry, or notify user
    pass
```

### 3. Monitor Spending

```python
# Regular budget checks
budget = agent.get_budget_status()
if budget["remaining_budget"] / budget["daily_budget"] < 0.1:
    # Send alert: budget running low
    pass
```

### 4. Use Appropriate SDK Level

- **Simple tasks** → MNEEAgent
- **Custom workflows** → PaymentSDK
- **Multi-agent coordination** → SwarmSDK

## Troubleshooting

### Issue: "Agent not found in configuration"

**Solution:** Add your agent to `config/agents.yaml`:

```yaml
agents:
  - id: "my-agent"
    priority: "MEDIUM"
    dailyBudget: 50.0
    maxPerCall: 5.0
```

### Issue: "Guardian Service not reachable"

**Solution:** Start Guardian Service:

```bash
cd backend/guardian
./start_guardian.sh
```

### Issue: "Policy denied: Insufficient budget"

**Solution:** Check budget and wait for daily reset, or increase budget in config.

## API Reference

See individual class docstrings for detailed API documentation:

- `MNEEAgent` - High-level agent interface
- `PaymentSDK` - Direct payment control
- `SwarmSDK` - Multi-agent orchestration

## Support

- **Documentation:** See `/backend/` READMEs
- **Examples:** See `examples/` directory
- **Issues:** GitHub Issues

## License

MIT License
