# MNEE Nexus Demo Script

**Duration**: 5-7 minutes
**Target**: MNEE Hackathon judges
**Focus**: Show real AI agent payment coordination with MNEE

---

## Pre-Demo Checklist

```bash
# 1. Start all services
./start_all.sh

# 2. Verify services are running
./start_all.sh status

# 3. Open browser to dashboard
open http://localhost:3000

# 4. Clear previous demo data (optional)
curl -X POST http://localhost:8000/reset
```

---

## Demo Flow (4-5 minutes)

### Scene 1: Introduction (0:00 - 0:30)

**Narration:**
> "MNEE Nexus is a payment orchestration layer for AI agents. It solves a critical problem: how do multiple AI agents share a budget, pay for services, and coordinate payments between each other - all using MNEE stablecoin."

**Screen:** Show the Overview dashboard with:
- Treasury balance
- Agent fleet cards
- Real-time WebSocket indicator (LIVE)

---

### Scene 2: Agent Fleet Overview (0:30 - 1:00)

**Action:** Click on "Agent Fleet" tab

**Narration:**
> "Here's our AI agent fleet. Each agent has its own role and budget:
> - **User Agent** - handles user requests, high priority, 100 MNEE daily budget
> - **Designer Agent** - specialized for image generation
> - **Analyst Agent** - data analysis tasks
> - **Archivist Agent** - log storage, lowest priority"

**Demo Actions:**
1. Hover over an agent card to show details
2. Click "Edit Budget" on one agent
3. Change budget from 50 to 75 MNEE
4. Show the budget update reflected immediately

---

### Scene 3: Live Ops - AI Agent Interaction (1:00 - 2:00)

**Action:** Click on "Live Ops" tab

**Narration:**
> "Let's see the agents in action. I'll ask the User Agent to generate an image."

**Type in terminal:**
```
Generate a futuristic logo for MNEE cryptocurrency
```

**Narration (while processing):**
> "Watch what happens:
> 1. The Policy Engine checks if this agent has budget
> 2. Guardian Service signs the MNEE payment
> 3. The ImageGen provider receives payment and generates the image
> 4. Transaction is recorded on-chain"

**Show:**
- Terminal output showing policy decision
- Transaction appearing in the Ledger
- Agent's daily spend updating

---

### Scene 4: A2A Network - Agent Collaboration (2:00 - 2:45)

**Action:** Click on "A2A Network" tab

**Narration:**
> "This is where it gets interesting. Agents can pay EACH OTHER for services.
> Let's say the Designer Agent needs data analysis from the Analyst Agent."

**Demo Actions:**
1. Show the A2A network visualization
2. Execute an A2A payment:
   - From: startup-designer
   - To: startup-analyst
   - Amount: 5 MNEE
   - Task: "Analyze design trends"
3. Show the transfer appearing in real-time
4. Show both agents' balances updating

**Narration:**
> "This creates a decentralized AI labor market where agents can hire each other and pay in MNEE."

---

### Scene 5: Escrow Manager - Trustless Transactions (2:45 - 3:30)

**Action:** Click on "Escrow Manager" tab

**Narration:**
> "For larger tasks, we use escrow. The payer locks MNEE, the worker completes the task, a verifier checks the work, and funds are released automatically."

**Show existing escrows:**
- Point out different statuses (created, verifying, released)
- Show the escrow flow diagram

**Demo Actions:**
1. Show an escrow in "verifying" status
2. Explain: "This task is being verified by our AI verifier"
3. If available, show dispute button and explain the flow

---

### Scene 6: Workflow Orchestration (3:30 - 4:45)

**Action:** Click on "Workflows" tab

**Narration:**
> "Now let me show our most powerful feature: Multi-Agent Workflow Orchestration.
> This enables defining pipelines where multiple agents collaborate on complex tasks,
> with automatic escrow handoffs between each step."

**Demo Actions:**
1. Show the workflow template selector
2. Select "Content Creation Pipeline"
3. Explain the pipeline:
   > "This workflow has three steps:
   > - **Writer** (analyst) creates the content - 2 MNEE
   > - **Designer** adds visuals - 3 MNEE
   > - **Reviewer** validates quality - 0.5 MNEE
   > Total: 5.5 MNEE with automatic escrow at each step"

4. Click "Start Workflow"

#### Coordination Phase (NEW)

**Narration (when Agent Coordination panel appears):**
> "First, watch the Agent Coordination phase. The system is collecting bids from all available agents for each capability. This is a real-time labor market for AI agents."

**Show:**
- Animated bid cards appearing for each capability
- Score breakdown: Price Score, Reputation Score, Success Rate
- Star ratings and task history
- **Winner selection** with highlighted reasoning

> "Notice how the system selects agents based on weighted criteria: price, reputation, and reliability. The winning agent for each step is chosen automatically with a clear explanation of why."

#### Execution Phase

5. Show the pipeline visualization animating:
   - Each step card pulses when running
   - Escrow status shows "locked" then "released"
   - Progress bar advances
   - Cost tracker updates
   - **TX hashes appear with links to block explorer**
   - **Selection reason shows WHY each agent was chosen**

**Narration (while running):**
> "Watch how each step:
> 1. Locks MNEE in escrow - creating a real escrow record
> 2. Executes A2A payment from customer to merchant agent
> 3. Agent performs the task using **real AI generation**
> 4. Verifies output quality
> 5. Releases escrow funds
> All transactions are recorded on-chain with verifiable TX hashes."

6. **Click on a completed step to expand output** (NEW)

**Narration:**
> "Now look at this - click any completed step to see the actual AI-generated output.
> This isn't mock data. The Writer agent used LLM to generate a real marketing draft.
> You can see the title, content, key points, and even copy the content to clipboard."

**Show:**
- Expandable output cards with role-specific formatting
- Writer output: Title, content, sections, word count
- Designer output: Color palette, asset descriptions
- Reviewer output: Score, strengths, improvements, verdict
- **"AI Generated" vs "Mock Data" badge** distinguishing LLM outputs

**Key Demo Points:**
> 1. "Unlike simulated demos, these are REAL MNEE payments. Click any TX hash to verify."
> 2. "The outputs are generated by actual AI - not pre-written scripts."
> 3. "The coordination phase shows WHY each agent was selected - full transparency."

---

### Scene 7: Policy Enforcement (4:45 - 5:15)

**Action:** Click on "Policy Logs" tab

**Narration:**
> "Every transaction goes through our Policy Engine. Let me show what happens when an agent exceeds its budget."

**Demo Actions:**
1. Go back to Live Ops
2. Try a command that would exceed budget:
   ```
   Generate 100 high-resolution images
   ```
3. Show the DENY decision in Policy Logs
4. Explain risk levels: RISK_OK, RISK_REVIEW, RISK_BLOCK

**Narration:**
> "The system automatically blocks overspending, detects suspicious patterns, and enforces budget limits - all off-chain for speed, with on-chain settlement for security."

---

### Scene 8: Architecture Summary (5:15 - 5:45)

**Show Overview tab again**

**Narration:**
> "To summarize what makes MNEE Nexus unique:
>
> 1. **Real MNEE Payments** - Using Hardhat fork of mainnet MNEE contract
> 2. **Multi-Agent Coordination** - Shared treasury with individual budgets
> 3. **A2A Payments** - Agents can pay each other for services
> 4. **Trustless Escrow** - Verification before payment release
> 5. **Workflow Orchestration** - Multi-agent pipelines with automatic handoffs
> 6. **Policy Enforcement** - Budget limits, risk detection, audit trails
>
> All built on MNEE stablecoin, enabling a new economy of AI agent collaboration."

---

## Backup Scenarios

### If WebSocket disconnects:
- Show the "POLL" indicator and explain fallback mechanism
- "The system gracefully degrades to API polling"

### If a service is slow:
- "Our retry logic with exponential backoff handles transient failures"

### If asked about scaling:
- "The architecture separates signing (Guardian) from orchestration (Policy Engine), allowing horizontal scaling"

---

## Key Talking Points

1. **Why MNEE?** - Stable, fast, low fees - perfect for micro-payments between AI agents

2. **Real Problem Solved** - AI agents need financial autonomy. Current solutions require human approval for every payment.

3. **Technical Innovation**:
   - Escrow-Verify-Release pattern
   - Off-chain policy, on-chain settlement
   - Guardian service for secure key isolation
   - Multi-agent workflow orchestration with automatic handoffs
   - **Agent Coordination with transparent selection (NEW)**
   - **Real AI-generated outputs, not mock data (NEW)**

4. **Market Potential** - Every AI agent deployment could use this infrastructure

5. **Solves Coordination Problems** (Hackathon Criteria):
   - Agent labor market with competitive bidding
   - Transparent selection reasoning
   - Real-time coordination visualization
   - Trustless handoffs between agents

---

## Technical Details (if asked)

| Component | Technology |
|-----------|------------|
| Smart Contracts | Solidity, Hardhat, MNEE ERC-20 |
| Backend | FastAPI, Python, Web3.py |
| Frontend | Next.js, React, TailwindCSS |
| AI Agents | LangChain, LangGraph |
| Real-time | WebSocket with fallback polling |
| Testing | Pytest (53 tests passing) |

---

## Demo Commands Quick Reference

```bash
# Start everything
./start_all.sh

# Check status
./start_all.sh status

# View logs
./start_all.sh logs backend

# Reset budgets
curl -X POST http://localhost:8000/reset

# Health check
curl http://localhost:8000/

# Run demo scenario
python scripts/demo_scenario.py
```
