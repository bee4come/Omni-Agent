# MNEE Nexus - Hackathon Features Summary

**Project**: MNEE Nexus - AI Agent Payment Orchestration
**Hackathon**: MNEE Hackathon 2024

---

## Executive Summary

MNEE Nexus is a payment orchestration layer that enables multiple AI agents to:
- Share a common MNEE treasury with individual budgets
- Pay for external services (ImageGen, Analytics, Storage)
- Pay each other for collaborative tasks (A2A payments)
- Use trustless escrow for verified task completion

---

## Core Features

### 1. Multi-Agent Treasury Management

| Feature | Description |
|---------|-------------|
| Shared Treasury | All agents draw from a common MNEE pool |
| Individual Budgets | Each agent has daily limits and per-call caps |
| Priority Levels | HIGH, MEDIUM, LOW priority for resource allocation |
| Real-time Tracking | Live dashboard showing spending across all agents |

### 2. Agent-to-Agent (A2A) Payments

- Agents can pay each other for services
- Creates a decentralized AI labor market
- On-chain settlement using MNEE
- Full transaction history and audit trail

### 3. Escrow-Verify-Release Pattern

```
Payer Agent -> Lock MNEE in Escrow
                    |
                    v
              Worker Agent completes task
                    |
                    v
              AI Verifier checks work
                    |
                    v
            Funds released or disputed
```

### 4. Policy Engine

- Off-chain policy evaluation for speed
- On-chain settlement for security
- Risk detection (burst patterns, first-time large calls)
- Automatic budget enforcement

---

## Technical Implementation

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (Next.js)                    │
│  Dashboard | Agent Fleet | Live Ops | Escrow Manager    │
└─────────────────────────────────────────────────────────┘
                           │ WebSocket + REST
                           ▼
┌─────────────────────────────────────────────────────────┐
│                   Backend (FastAPI)                      │
│  Policy Engine | Payment Client | A2A Client | Registry │
└─────────────────────────────────────────────────────────┘
        │                    │                    │
        ▼                    ▼                    ▼
┌───────────────┐  ┌─────────────────┐  ┌────────────────┐
│   Guardian    │  │  Service Provs  │  │   Hardhat      │
│   (Key Mgmt)  │  │  (ImageGen...)  │  │   (MNEE Fork)  │
└───────────────┘  └─────────────────┘  └────────────────┘
```

### Technology Stack

| Layer | Technologies |
|-------|--------------|
| Smart Contracts | Solidity, Hardhat, MNEE ERC-20 |
| Backend | FastAPI, Python 3.10+, Web3.py |
| Frontend | Next.js 14, React 18, TailwindCSS |
| AI Agents | LangChain, LangGraph |
| Database | SQLite (SQLAlchemy) |
| Real-time | WebSocket with polling fallback |
| Testing | Pytest (53+ tests) |

---

## Hackathon Improvements

### Day 1-2: Frontend UX
- [x] Mobile responsive design with hamburger menu
- [x] Framer Motion animations (page transitions, card animations)
- [x] ARIA accessibility roles and keyboard navigation
- [x] Onboarding modal for first-time users
- [x] Edit Budget / Pause Agent functionality
- [x] Approve / Dispute buttons for escrows

### Day 3-4: Backend Infrastructure
- [x] Pytest test infrastructure (53 tests passing)
- [x] SQLite persistence layer with SQLAlchemy
- [x] Retry logic with exponential backoff
- [x] Policy Engine tests (budget, risk, evaluation)
- [x] Database repository tests

### Day 5: Real-time Features
- [x] WebSocket endpoint for live updates
- [x] WebSocket client with auto-reconnection
- [x] Connection status indicator (LIVE/SYNC/POLL)
- [x] Graceful fallback to API polling

### Day 6-7: Demo & Documentation
- [x] Demo script with timestamps (docs/DEMO_SCRIPT.md)
- [x] Automated demo scenario (scripts/demo_scenario.py)
- [x] Full API documentation (docs/API.md)
- [x] Feature summary (this document)

---

## Key Innovations

### 1. Guardian Service Architecture
Isolated key management service that:
- Holds treasury private key in isolated process
- Exposes only quote/pay endpoints
- Never exposes signing capability to other services

### 2. Service Call Hash
Anti-spoofing mechanism that binds:
- Service ID + Agent ID + Task ID + Payload
- Enables on-chain/off-chain reconciliation
- Prevents payment replay attacks

### 3. Risk Detection
Pattern-based risk scoring:
- Burst detection (>5 calls/minute)
- First-time large call flagging
- Provider failure tracking

---

## Demo Highlights

1. **Dashboard Overview**: Real-time treasury and agent status
2. **Live Ops**: Interactive terminal for agent commands
3. **A2A Payments**: Agents paying each other on-chain
4. **Escrow Flow**: Trustless task verification
5. **Policy Enforcement**: Budget denial demonstration

---

## Running the Demo

```bash
# Start all services
./start_all.sh

# Check status
./start_all.sh status

# Run automated demo
python scripts/demo_scenario.py

# Open dashboard
open http://localhost:3000
```

---

## Test Coverage

```
tests/test_policy_engine.py  - 19 tests (budget, risk, evaluation)
tests/test_database.py       - 15 tests (CRUD, transactions, escrows)
tests/test_retry.py          - 19 tests (backoff, async, decorators)
───────────────────────────────────────────────────────────────────
Total: 53 tests passing
```

---

## Future Roadmap

1. **Production Deployment**: Docker, Kubernetes orchestration
2. **Multi-chain Support**: Beyond MNEE to other stablecoins
3. **Agent Marketplace**: Public registry with reputation system
4. **Advanced Verification**: ML-based task quality assessment
5. **Governance**: DAO for policy parameter updates

---

## Team

Built for MNEE Hackathon 2024

---

## Links

- [Demo Video](#) (coming soon)
- [GitHub Repository](#)
- [API Documentation](./API.md)
- [Demo Script](./DEMO_SCRIPT.md)
