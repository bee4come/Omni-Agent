<!-- OPENSPEC:START -->
# OpenSpec Instructions

These instructions are for AI assistants working in this project.

Always open `@/openspec/AGENTS.md` when the request:
- Mentions planning or proposals (words like proposal, spec, change, plan)
- Introduces new capabilities, breaking changes, architecture shifts, or big performance/security work
- Sounds ambiguous and you need the authoritative spec before coding

Use `@/openspec/AGENTS.md` to learn:
- How to create and apply change proposals
- Spec format and conventions
- Project structure and guidelines

Keep this managed block so 'openspec update' can refresh the instructions.

<!-- OPENSPEC:END -->

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**MNEE Nexus / Omni-Agent** is a programmable payment orchestration system for AI Agents built on MNEE stablecoin. Multiple AI Agents share an MNEE treasury pool, with budget/policy/priority management for pay-per-task service calls.

## Architecture

### Core Data Flow

```
User Request → Planner → Guardian (risk check) → EscrowLock → Executor → Verifier → EscrowRelease → Summarizer
```

The complete flow is defined in `backend/agents/graph.py` using LangGraph's StateGraph. All state flows through `GraphState` (`backend/agents/state.py`).

### Four-Layer Architecture

1. **Smart Contracts** (`contracts/`)
   - `MNEEPaymentRouter.sol` - Handles MNEE payments, emits `PaymentExecuted` events
   - `MNEEServiceRegistry.sol` - Service provider registration and pricing
   - `MNEEAgentWallet.sol` - Agent wallet management for A2A payments
   - Uses Hardhat mainnet fork of real MNEE contract (`0x8ccedbAe4916b79da7F3F612EfB2EB93A2bFD6cF`)

2. **Backend Orchestration** (`backend/`)
   - **Guardian Service** (`guardian/service.py`) - ONLY service holding `TREASURY_PRIVATE_KEY`, port 8100
   - **Policy Engine** (`policy/engine.py`) - Budget/priority enforcement, `check_policy()` returns ALLOW/DENY/DOWNGRADE
   - **Payment Client** (`payment/client.py`) - Calls Guardian for payments, never holds private keys
   - **A2A Client** (`payment/a2a_client.py`) - Agent-to-Agent payment execution
   - **LangGraph Nodes** (`agents/nodes/`) - planner, guardian, executor, verifier, escrow_lock, escrow_release, feedback, summarizer
   - **Swarm Architecture** (`agents/swarm/`) - Multi-agent coordination: Manager → Customer → Merchant → Treasurer

3. **Service Providers** (`providers/`) - Independent FastAPI services
   - `imagegen/` (port 8001) - 1.0 MNEE/call
   - `price_oracle/` (port 8002) - 0.05 MNEE/query
   - `batch_compute/` (port 8003) - 3.0 MNEE/task
   - `log_archive/` (port 8004) - 0.01 MNEE/log

4. **Frontend** (`frontend/`) - Next.js 14 + React 18 + TailwindCSS

## Development Commands

### Quick Start

```bash
./start_all.sh              # Start all services (Hardhat + contracts + providers + backend)
./start_all.sh status       # Check status
./start_all.sh logs backend # View specific logs
./start_all.sh stop         # Stop all services
```

### Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000   # Dev server

# Tests
python test_api.py          # API integration test
python test_graph.py        # LangGraph workflow test
python test_swarm.py        # Swarm architecture test
python verify_langchain_v1.py  # LangChain 1.0 compatibility check
```

### Smart Contracts

```bash
cd contracts
npm ci
npx hardhat compile                              # Compile
npx hardhat test                                 # Run tests
npx hardhat coverage                             # Coverage report
npx hardhat run scripts/deploy.js --network localhost  # Deploy
npx hardhat console --network localhost          # Interactive console
```

### Frontend

```bash
cd frontend
npm install
npm run dev     # Dev server on port 3000
npm run build   # Production build
npm run lint    # ESLint
```

### Guardian Service (Isolated Key Management)

```bash
cd backend
python -m guardian.service  # Start on port 8100
# Test: curl http://localhost:8100/guardian/balance
```

**Security:** Guardian is the ONLY service holding `TREASURY_PRIVATE_KEY`. Payment Client calls Guardian's HTTP API for all signing operations.

## Configuration

### Agent Budgets (`config/agents.yaml`)

```yaml
agents:
  - id: "user-agent"
    priority: "HIGH"      # HIGH/MEDIUM/LOW
    dailyBudget: 100.0    # MNEE per day
    maxPerCall: 10.0      # Max single transaction
```

### Services (`config/services.yaml`)

```yaml
services:
  - id: "IMAGE_GEN_PREMIUM"
    unitPrice: 1.0
    providerAddress: "0x..."
    active: true
```

### Environment (`backend/.env`)

Required variables:
- `ETH_RPC_URL` - Hardhat node (default: `http://127.0.0.1:8545`)
- `MNEE_TOKEN_ADDRESS` - Real MNEE contract address
- `PAYMENT_ROUTER_ADDRESS`, `SERVICE_REGISTRY_ADDRESS` - From deployment output
- `TREASURY_PRIVATE_KEY` - Hardhat test account (used only by Guardian)
- LLM keys: `OPENAI_API_KEY` or `AWS_ACCESS_KEY_ID`/`AWS_SECRET_ACCESS_KEY`

## Key Workflows

### Adding a New Service Provider

1. Register in `MNEEServiceRegistry` contract
2. Add to `config/services.yaml`
3. Create FastAPI service in `providers/`
4. Define tool in `backend/agents/tools/definitions.py`
5. Register in `backend/agents/omni_agent.py`

### Payment Flow (Escrow-Verify-Release Protocol)

```
1. Policy Check      -> PolicyEngine.check_policy() returns ALLOW/DENY/DOWNGRADE
2. Escrow Lock       -> Funds locked via EscrowManager
3. Guardian Pay      -> Guardian signs and executes on-chain payment
4. Service Execution -> Call provider HTTP API
5. Verification      -> Verifier validates output
6. Escrow Release    -> Funds released to merchant or refunded
```

### Policy Engine (`backend/policy/engine.py`)

- `check_policy()` validates daily budget and per-call limits
- Priority levels: HIGH/MEDIUM/LOW
- Automatic service downgrade when budget is insufficient

**Important:** Complex policy logic stays off-chain. Smart contracts only handle basic payment routing.

## Technical Details

### Hardhat Fork

- Forks real MNEE contract `0x8ccedbAe4916b79da7F3F612EfB2EB93A2bFD6cF` from Ethereum mainnet
- Uses `impersonateAccount` to acquire MNEE tokens (zero-cost testing)
- Config: `contracts/hardhat.config.ts` `forking` section

### LangGraph Integration

- Main workflow: `backend/agents/graph.py` - builds `StateGraph` with all nodes
- State definition: `backend/agents/state.py` - `GraphState`, `StepRecord`, `EscrowRecord`
- Tool wrapper: `backend/payment/wrapper.py` - enforces payment on every tool call
- Supports OpenAI and AWS Bedrock LLMs

### A2A (Agent-to-Agent) Commerce

- `backend/payment/a2a_client.py` - handles inter-agent payments
- `backend/agents/registry.py` - agent discovery with capabilities and reputation
- `backend/agents/nodes/escrow.py` - trustless transactions via escrow
- `backend/agents/nodes/verifier.py` - output verification before fund release

## Service Ports

| Service | Port | Purpose |
|---------|------|---------|
| Hardhat Node | 8545 | Ethereum RPC |
| Backend API | 8000 | Main API (Swagger at /docs) |
| Guardian | 8100 | Isolated key management |
| ImageGen | 8001 | Image generation |
| PriceOracle | 8002 | Price data |
| BatchCompute | 8003 | Batch computation |
| LogArchive | 8004 | Log storage |
| Frontend | 3000 | Next.js UI |

## API Endpoints

```bash
# Health & Status
GET  /                    # Service info
GET  /treasury            # Budget status across all agents
GET  /agents              # List all agents
GET  /services            # List all services

# Chat (main agent interaction)
POST /chat                # {"agent_id": "user-agent", "message": "..."}

# A2A Payments
POST /a2a/pay             # Execute agent-to-agent payment
GET  /a2a/transfers       # Recent A2A transfers
GET  /a2a/balances        # All agent wallet balances

# Agent Registry (Labor Market)
GET  /registry/agents     # All registered agents
GET  /registry/find?capability=image_gen  # Find by capability
GET  /registry/select?capability=...      # Select best agent

# Escrow
GET  /escrow/list         # All escrow transactions
POST /escrow/{id}/dispute # Raise dispute

# Policy & Logs
GET  /policy/logs         # Recent policy decisions
POST /reset               # Reset daily budgets
```

## Troubleshooting

- **Services won't start**: `./start_all.sh status`, check `logs/` directory
- **Contract errors**: Verify Hardhat node running, check `.env` addresses
- **Policy denials**: Check `config/agents.yaml`, view `/policy/logs`, use `/reset`
- **Port conflicts**: `lsof -i :PORT`

## Testing

### Smart Contract Tests

```bash
cd contracts
npx hardhat test                    # Run all tests
npx hardhat test test/MNEEEscrow.test.ts  # Run specific test
npx hardhat coverage               # Generate coverage report
```

Test files:
- `test/MNEEServiceRegistry.test.ts` - Service registration, updates, access control
- `test/MNEEPaymentRouter.test.ts` - Payment execution, events, edge cases
- `test/MNEEAgentWallet.test.ts` - A2A payments, agent management, withdrawals
- `test/MNEEEscrow.test.ts` - Escrow-Verify-Release protocol, disputes

### Demo Script

```bash
./scripts/demo.sh              # Full interactive demo
./scripts/demo.sh treasury     # Just treasury demo
./scripts/demo.sh a2a          # Just A2A payment demo
./scripts/demo.sh failure      # Budget exhaustion scenario
```

## Code Conventions

- All code and comments must be in English (no Chinese characters or emojis in code)
- After modifying contracts, redeploy and update `backend/.env`
- All logs saved to `logs/` directory
- Architecture diagram: `docs/ARCHITECTURE.md`