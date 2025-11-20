# MNEE Nexus Backend

FastAPI-based backend orchestration layer for the MNEE Nexus / Omni-Agent system.

## Architecture

```
backend/
├── app/
│   └── main.py              # FastAPI application with all REST endpoints
├── agents/
│   ├── omni_agent.py        # Main agent orchestrator
│   └── tools/
│       └── definitions.py    # Tool definitions (ImageGen, PriceOracle, etc.)
├── payment/
│   ├── client.py            # Web3 payment client
│   └── wrapper.py           # PaidToolWrapper - enforces policy + payment
├── policy/
│   ├── engine.py            # Policy engine - budget & priority checks
│   └── logger.py            # System logger for transactions & policy decisions
├── .env                     # Environment configuration (not in git)
├── .env.example             # Example configuration template
└── requirements.txt         # Python dependencies
```

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
