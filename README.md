# MNEE Agent Cost & Billing Hub

**The Financial Operating System for AI Agent Teams**

> Built for MNEE Hackathon 2025 - AI & Agent Payments Track

Stop runaway AI agent spending. Get centralized budget control, policy enforcement, and complete transaction auditing for teams running multiple autonomous agents.

---

## The Real Problem

Your team has multiple AI agents calling expensive APIs:
- Customer support chatbot
- Nightly data processing
- On-demand report generation  

**Without centralized control:**
- Agent goes into infinite loop, burns $1000 overnight
- Finance has no idea which project spent what
- No way to enforce spending limits per agent/project

**Result:** Budget chaos and zero accountability.

---

## Our Solution

**MNEE Agent Cost & Billing Hub** gives you:

1. **Unified MNEE Treasury** - All agents draw from one pool
2. **Project-Level Budgets** - Set daily caps (e.g., "Chatbot: 50 MNEE/day")
3. **Agent-Level Limits** - Prevent individual agent mistakes
4. **Real-Time Enforcement** - Every transaction: `Policy → Guardian → Payment`
5. **Complete Audit Trail** - Who spent what, when, and why

---

## Quick Demo

```bash
# Start everything
./start_all.sh start

# Test API
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"agent_id":"user-agent","message":"Generate a logo"}'

# Check budget status
curl http://localhost:8000/treasury

# View frontend
open http://localhost:3000
```

---

## How It Works

```
User: "Generate a marketing image"
    ↓
[Planner] → Break into steps: "Use IMAGE_GEN service, cost ~1 MNEE"
    ↓
[Guardian] → Check budgets:
    - Project has 45/50 MNEE left today
    - Agent has 8/10 MNEE left today  
    - Service allowed for this project
    → Decision: ALLOW
    ↓
[Executor] → Pay 1 MNEE via MNEE contract → Get image from provider
    ↓
[Auditor] → Record: agent=user-agent, service=IMAGE_GEN, cost=1 MNEE, tx=0x...
```

---

## Key Features

### 1. Agent-to-Agent (A2A) Payments

The killer feature: Agents can **hire other agents** and pay them with MNEE.

```
User: "Analyze market and generate report"
    ↓
[Analyst Agent] → Needs market data
    ↓ pays 0.5 MNEE
[Data Agent] → Delivers data
    ↓
[Analyst Agent] → Needs visualization
    ↓ pays 1.0 MNEE  
[Chart Agent] → Delivers charts
    ↓
[Analyst Agent] → Completes report
```

All payments visible in real-time on the **A2A Network** visualization.

### 2. Hierarchical Budget Control

```
Project: "Marketing Team" (100 MNEE/day)
├── social-media-agent (20 MNEE/day, HIGH priority)
└── content-generator (10 MNEE/day, NORMAL priority)
```

### 3. Policy Enforcement

Every transaction checked against:
- Service whitelist (can this project use this API?)
- Single transaction limit (max spend per call)
- Daily budget (agent + project level)
- Risk patterns (burst detection, anomalies)

### 4. Guardian Service

Secure key management with TEE-ready architecture:
- Private keys **never** exposed to application code
- All signing operations go through Guardian
- Complete audit trail of every transaction

### 5. Real-Time Auditing

```json
{
  "agent_id": "user-agent",
  "service_id": "IMAGE_GEN",
  "amount_mnee": 1.0,
  "policy_action": "ALLOW",
  "tx_hash": "0x...",
  "timestamp": "2025-11-25T10:30:00Z"
}
```

### 4. Guardian Risk Engine

Automatically blocks:
- Burst attacks (>5 calls/minute)
- First-time large expenses from low-priority agents
- Requests after budget exhaustion

---

## Setup

### Prerequisites
- Node.js 18+, Python 3.10+
- (Optional) LLM API key (OpenAI/Google/AWS Bedrock)

### Installation

```bash
git clone https://github.com/bee4come/Omni-Agent.git
cd Omni-Agent

# Install backend
cd backend && pip install -r requirements.txt

# Install contracts
cd ../contracts && npm install

# Install frontend
cd ../frontend && npm install

# Configure
cp backend/.env.example backend/.env
# Edit backend/.env with your settings

# Start all services
./start_all.sh start
```

Services will run on:
- Backend API: http://localhost:8000
- Guardian: http://localhost:8100  
- Frontend: http://localhost:3000
- Hardhat: http://localhost:8545

---

## Configuration

### Set Project Budgets

Edit `config/agents.yaml`:

```yaml
agents:
  - id: "user-agent"
    priority: "HIGH"
    dailyBudget: 100.0
    maxPerCall: 50.0

  - id: "batch-agent"
    priority: "LOW"
    dailyBudget: 30.0
    maxPerCall: 5.0
```

### Configure Services

Edit `config/services.yaml`:

```yaml
services:
  - id: "IMAGE_GEN_PREMIUM"
    unitPrice: 1.0
    providerAddress: "0x..."
    active: true
```

---

## Architecture

```
backend/
├── agents/           # LangGraph orchestration
│   ├── state.py     # GraphState, StepRecord
│   ├── nodes/       # Planner, Guardian, Executor
│   └── graph.py     # Workflow definition
├── policy/          # Budget enforcement
│   ├── engine.py    # PolicyEngine (main logic)
│   └── models.py    # ProjectPolicy, AgentPolicy
├── guardian/        # Secure key management
│   └── service.py   # Isolated payment signing
└── payment/         # Payment orchestration
    ├── wrapper.py   # Unified enforcement
    └── client.py    # Guardian interface

frontend/
├── components/
│   ├── LiveGraph.tsx    # Execution visualization
│   ├── AuditLog.tsx     # Transaction timeline
│   └── Dashboard.tsx    # Budget overview

contracts/
├── MNEEPaymentRouter.sol
└── MNEEServiceRegistry.sol
```

---

## API Reference

### POST /chat
Execute agent task with budget enforcement.

```bash
curl -X POST http://localhost:8000/chat \
  -d '{"agent_id":"user-agent","message":"Check ETH price"}'
```

### GET /treasury
View budget status across all projects/agents.

### GET /policy/logs
View recent policy decisions (ALLOW/DENY/DOWNGRADE).

---

## Real Use Cases

### Use Case 1: Prevent Runaway Spending
**Problem**: Dev agent accidentally starts infinite loop  
**Solution**: Daily budget cap at 5 MNEE, automatically denies after limit

### Use Case 2: Project Attribution
**Problem**: Finance can't tell which project burned budget  
**Solution**: All spending tagged with project_id, exportable to CSV

### Use Case 3: Service Restrictions
**Problem**: Production agents calling expensive test APIs  
**Solution**: Project whitelist blocks unauthorized services

---

## Testing

```bash
# Backend tests
cd backend
python test_graph.py

# Verify LangChain 1.0 compatibility
python verify_langchain_v1.py
```

---

## Documentation

- `LATEST_UPDATES.md` - Recent feature additions
- `GRAPH_ARCHITECTURE.md` - LangGraph node structure
- `LANGCHAIN_V1_COMPATIBILITY.md` - LangChain 1.0 migration
- `GUARDIAN_MIGRATION.md` - Guardian service setup
- `HARDHAT_FORK_GUIDE.md` - Blockchain setup

---

## Roadmap

### Phase 1: Core Platform (Current)
- Project/agent budget hierarchy
- Multi-layer policy enforcement
- Risk engine with burst detection
- Real-time audit trail

### Phase 2: Advanced Features
- ML-based anomaly detection
- Multi-wallet support
- Invoice settlement (net-30)
- DAO governance

### Phase 3: Enterprise
- SSO integration
- RBAC (role-based access)
- Compliance reporting
- Multi-chain support

---

## FAQ

**Q: Do I need real MNEE tokens?**  
A: No. Uses Hardhat fork with mainnet contract for zero-cost testing.

**Q: What if my agent needs a new service?**  
A: Add to `config/services.yaml` and register in ServiceRegistry contract.

**Q: Can I use without LLMs?**  
A: Yes. Planner has keyword-based fallback.

---

## License

MIT License

---

## Contributing

1. Fork repository
2. Create feature branch
3. Submit pull request

---

## Contact

- GitHub: https://github.com/bee4come/Omni-Agent
- Issues: https://github.com/bee4come/Omni-Agent/issues

---

**Built for MNEE Hackathon 2025**

Solving real coordination problems for AI agent teams.
