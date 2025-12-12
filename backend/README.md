# MNEE Nexus Backend

FastAPI-based backend orchestration layer for the MNEE Nexus / Omni-Agent system.

## Architecture

```
backend/
├── app/
│   └── main.py              # FastAPI application with all REST endpoints
├── agents/
│   ├── omni_agent.py        # Main agent orchestrator
│   ├── graph.py             # LangGraph workflow definition
│   ├── registry.py          # AgentCard + AgentRegistry for dynamic discovery
│   ├── state.py             # GraphState, StepRecord, EscrowRecord, A2APaymentRecord
│   ├── nodes/
│   │   ├── planner.py       # Task decomposition with agent delegation
│   │   ├── guardian.py      # Policy pre-flight check
│   │   ├── escrow.py        # Escrow lock/release for trustless transactions
│   │   ├── executor.py      # Tool execution with A2A payments
│   │   ├── verifier.py      # Three-layer verification (Local/AI/Oracle)
│   │   ├── summarizer.py    # Result summarization
│   │   └── feedback.py      # Policy feedback
│   └── tools/
│       └── definitions.py    # Tool definitions (ImageGen, PriceOracle, etc.)
├── payment/
│   ├── client.py            # Web3 payment client (Service Provider payments)
│   ├── a2a_client.py        # A2A payment client (Agent-to-Agent payments)
│   └── wrapper.py           # PaidToolWrapper - enforces policy + payment
├── policy/
│   ├── engine.py            # Policy engine - budget & priority checks
│   └── logger.py            # System logger for transactions & policy decisions
├── .env                     # Environment configuration (not in git)
├── .env.example             # Example configuration template
└── requirements.txt         # Python dependencies
```

## A2A (Agent-to-Agent) Payment Flow

When a task requires multiple agents to collaborate, real MNEE transfers occur on-chain:

```
User Command: "Analyze competitor pricing and generate report"
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│  user-agent (CEO)                                       │
│  ┌─────────────────────────────────────────────────┐   │
│  │ Delegates to startup-analyst                     │   │
│  │ A2A Payment: 0.01 MNEE ─────────────────────────┼───┼─→ TX: 0xabc...
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│  startup-analyst                                        │
│  ┌─────────────────────────────────────────────────┐   │
│  │ Calls price_oracle service                       │   │
│  │ Service Payment: 0.05 MNEE ─────────────────────┼───┼─→ TX: 0xdef...
│  └─────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────┐   │
│  │ Calls batch_compute service                      │   │
│  │ Service Payment: 3.0 MNEE ──────────────────────┼───┼─→ TX: 0x123...
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

All payments are:
- **Real on-chain MNEE transfers**
- **Verifiable on Etherscan**
- **Recorded in transaction history**

## Escrow-Verify-Release Protocol

The decentralized Agent labor market uses trustless escrow for all transactions:

```
┌──────────────────────────────────────────────────────────────────────────┐
│                     ESCROW-VERIFY-RELEASE FLOW                           │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  Planner ─→ Guardian ─→ EscrowLock ─→ Executor ─→ Verifier ─→ EscrowRelease
│                              │                        │              │
│                              │                        │              │
│                              ▼                        ▼              ▼
│                         Lock MNEE              Verify Output    Release/Refund
│                         in Escrow              (3-Layer)        based on result
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘

Three-Layer Verification:
├── Layer 1: Local Optimistic (95% of cases) - Fast, cheap heuristics
├── Layer 2: AI Network (4% of cases) - Autonolas Mech consensus
└── Layer 3: Oracle Arbitration (1% of cases) - UMA DVM human voting
```

## Agent Registry & Discovery

Agents advertise capabilities and pricing via `AgentCard`:

```python
AgentCard(
    agent_id="startup-designer",
    capabilities=["image_gen", "logo_creation", "banner_design"],
    pricing={"image_gen": 1.0, "logo_creation": 3.0},
    reputation_score=4.5,
    success_rate=0.92
)
```

Selection algorithm balances:
- **Price**: Lower is better
- **Reputation**: Higher rating preferred
- **Success Rate**: Historical reliability

## Quick Start

### 1. Setup

```bash
# Copy and configure environment variables
cp .env.example .env
# Edit .env and fill in your keys

# Install dependencies
pip install -r requirements.txt
```

### 2. Run the Backend

**Option A: Using the startup script**
```bash
chmod +x start_backend.sh
./start_backend.sh
```

**Option B: Manual start**
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at:
- **API Endpoint**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **OpenAPI Spec**: http://localhost:8000/openapi.json

## API Endpoints

### Core Endpoints

#### `POST /chat`
Send a message to an agent. The agent will use paid tools as needed.

**Request:**
```json
{
  "agent_id": "user-agent",
  "message": "Generate a cyberpunk avatar"
}
```

**Response:**
```json
{
  "response": "Here is your image: https://...",
  "agent_id": "user-agent"
}
```

---

### Treasury & Agents

#### `GET /treasury`
Get overall treasury status including all agents' budgets and spending.

**Response:**
```json
{
  "agents": {
    "user-agent": {
      "id": "user-agent",
      "priority": "HIGH",
      "dailyBudget": 100.0,
      "currentDailySpend": 15.5,
      "remainingBudget": 84.5
    }
  },
  "totalAllocated": 180.0,
  "totalSpent": 25.5
}
```

#### `GET /agents`
List all configured agents.

#### `GET /agents/{agent_id}`
Get detailed info about a specific agent including its transaction history.

#### `PUT /agents/{agent_id}/budget`
Update an agent's budget configuration.

**Request:**
```json
{
  "daily_budget": 150.0,
  "max_per_call": 15.0
}
```

---

### Services

#### `GET /services`
List all configured service providers.

**Response:**
```json
{
  "services": [
    {
      "id": "IMAGE_GEN_PREMIUM",
      "unitPrice": 1.0,
      "providerAddress": "0x...",
      "active": true
    }
  ]
}
```

#### `GET /services/{service_id}`
Get detailed info about a specific service including revenue stats.

---

### Transactions & Logs

#### `GET /transactions?limit=50`
Get recent transaction history.

**Response:**
```json
{
  "transactions": [
    {
      "timestamp": "2024-11-20T02:15:30",
      "agent_id": "user-agent",
      "service_id": "IMAGE_GEN_PREMIUM",
      "task_id": "abc-123",
      "amount": 1.0,
      "tx_hash": "0x...",
      "status": "SUCCESS"
    }
  ]
}
```

#### `GET /policy/logs?limit=50`
Get recent policy decision logs (ALLOWED, REJECTED, DOWNGRADED).

**Response:**
```json
{
  "logs": [
    {
      "timestamp": "2024-11-20T02:15:30",
      "agent_id": "batch-agent",
      "service_id": "BATCH_COMPUTE",
      "action": "REJECTED",
      "reason": "Cost 3.0 exceeds maxPerCall 2.0",
      "cost": 3.0
    }
  ]
}
```

---

### Statistics

#### `GET /stats`
Get overall system statistics.

**Response:**
```json
{
  "transactions": {
    "total": 42,
    "successful": 40,
    "failed": 2
  },
  "policyActions": {
    "ALLOWED": 35,
    "REJECTED": 5,
    "DOWNGRADED": 2
  },
  "totalAllocatedBudget": 180.0,
  "totalSpent": 67.5,
  "serviceCount": 4,
  "agentCount": 3
}
```

---

### Utilities

#### `POST /reset`
Reset all agents' daily spending to 0 (simulates a new day).

---

### A2A (Agent-to-Agent) Payments

Real on-chain MNEE transfers between AI agents.

#### `POST /a2a/pay`
Execute an Agent-to-Agent payment on-chain.

**Request:**
```json
{
  "from_agent": "user-agent",
  "to_agent": "startup-analyst",
  "amount": 0.5,
  "task_description": "Analyze market data"
}
```

**Response:**
```json
{
  "success": true,
  "tx_hash": "0x...",
  "transfer_id": 1,
  "from_agent": "user-agent",
  "to_agent": "startup-analyst",
  "amount": 0.5
}
```

#### `GET /a2a/transfers?count=20`
Get recent A2A transfers for visualization.

**Response:**
```json
{
  "transfers": [
    {
      "transfer_id": 1,
      "from_agent": "user-agent",
      "to_agent": "startup-analyst",
      "amount": 0.5,
      "task_description": "Analyze market data",
      "tx_hash": "0x...",
      "timestamp": "2024-11-26T10:30:00"
    }
  ],
  "total_count": 10
}
```

#### `GET /a2a/balances`
Get all agent wallet balances from the smart contract.

**Response:**
```json
{
  "balances": {
    "user-agent": 99.5,
    "startup-designer": 100.0,
    "startup-analyst": 100.5,
    "startup-archivist": 100.0
  },
  "total": 400.0
}
```

#### `GET /a2a/agent/{agent_id}`
Get detailed info about an agent's wallet.

**Response:**
```json
{
  "registered": true,
  "name": "Primary User Agent",
  "balance": 99.5,
  "total_received": 100.0,
  "total_spent": 0.5
}
```

---

### Agent Registry (Decentralized Labor Market)

#### `GET /registry/agents`
List all registered agents with capabilities and pricing.

**Response:**
```json
{
  "agents": [
    {
      "agent_id": "startup-designer",
      "name": "Designer Agent",
      "capabilities": ["image_gen", "logo_creation", "banner_design"],
      "pricing": {"image_gen": 1.0, "logo_creation": 3.0},
      "reputation_score": 4.5,
      "success_rate": 0.92,
      "total_tasks_completed": 150
    }
  ],
  "market_stats": {
    "total_agents": 6,
    "available_agents": 6,
    "total_tasks_completed": 970,
    "avg_success_rate": 0.95
  }
}
```

#### `GET /registry/find?capability=image_gen`
Find agents that can handle a specific capability.

#### `GET /registry/select?capability=image_gen&price_weight=0.4&reputation_weight=0.4`
Select the best agent using weighted scoring algorithm.

---

### Escrow (Trustless Transactions)

#### `GET /escrow/list`
List all escrow transactions.

**Response:**
```json
{
  "escrows": [
    {
      "escrow_id": "ESC-a1b2c3d4",
      "task_id": "TASK-001",
      "customer_agent": "user-agent",
      "merchant_agent": "startup-designer",
      "amount": 1.5,
      "status": "released",
      "verification_score": 0.92,
      "verification_passed": true,
      "lock_tx_hash": "0x...",
      "release_tx_hash": "0x..."
    }
  ],
  "by_status": {
    "created": 1,
    "submitted": 0,
    "verifying": 1,
    "released": 5,
    "refunded": 0,
    "disputed": 0
  }
}
```

#### `GET /escrow/{escrow_id}`
Get details of a specific escrow.

#### `POST /escrow/{escrow_id}/dispute`
Raise a dispute for an escrow transaction.

**Request:**
```json
{
  "reason": "Output does not match requirements"
}
```

---

## Configuration

### Agent Configuration (`../config/agents.yaml`)

```yaml
agents:
  - id: "user-agent"
    priority: "HIGH"
    dailyBudget: 100.0
    maxPerCall: 10.0
```

### Service Configuration (`../config/services.yaml`)

```yaml
services:
  - id: "IMAGE_GEN_PREMIUM"
    unitPrice: 1.0
    providerAddress: "0x..."
    active: true
```

## Components Deep Dive

### Policy Engine

The `PolicyEngine` enforces:
- **Daily budgets** per agent
- **Per-call limits** per agent
- **Priority-based** resource allocation
- **Downgrade logic** when budgets are tight

### Payment Wrapper

The `PaidToolWrapper` wraps every tool with:
1. **Policy check** - Is this allowed?
2. **Payment execution** - Pay on-chain via MNEE
3. **Logging** - Record decision & transaction
4. **Tool execution** - Run the actual tool

### System Logger

Tracks two types of events:
1. **Policy Decisions** - ALLOWED, REJECTED, DOWNGRADED
2. **Transactions** - SUCCESS, FAILED, MOCK

## Development

### Adding a New Service

1. Add service config to `../config/services.yaml`
2. Implement provider endpoint (in `providers/` folder)
3. Create tool function in `agents/tools/definitions.py`
4. Register tool in `OmniAgent.create_agent()`

### Adding a New Agent

1. Add agent config to `../config/agents.yaml`
2. Optionally customize behavior in `OmniAgent`

## Environment Variables

See `.env.example` for all available configuration options.

Key variables:
- `ETH_RPC_URL` - Ethereum RPC endpoint
- `MNEE_TOKEN_ADDRESS` - MNEE ERC-20 contract address
- `PAYMENT_ROUTER_ADDRESS` - PaymentRouter contract address
- `TREASURY_PRIVATE_KEY` - Treasury wallet private key
- `AWS_ACCESS_KEY_ID` / `OPENAI_API_KEY` - LLM credentials

## Dependencies

Main dependencies:
- **FastAPI** - Web framework
- **LangChain** - Agent orchestration
- **Web3.py** - Ethereum interaction
- **Pydantic** - Data validation
- **PyYAML** - Config parsing

See `requirements.txt` for full list.

## License

MIT License
