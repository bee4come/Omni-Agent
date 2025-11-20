# MNEE Nexus / Omni-Agent
**Programmable Payment Orchestrator for AI Agents**

---

## Elevator Pitch

MNEE Nexus / Omni-Agent is an **agent-native payment OS** that lets multiple AI agents share a single MNEE treasury and pay different service providers on a **pay-per-task** basis.

Instead of hard-coding API keys and hidden billing into each tool, we turn **every tool and API into a paid service provider** that is settled in MNEE on Ethereum.  
Agents must respect budgets, policies, and priorities when they spend — just like humans and organizations do.

---

## Inspiration

Today, most AI agents look powerful, but financially they are children:

- They **don’t have their own money**.
- They **can’t pass KYC** or get a credit card.
- They rely on opaque, centralized billing controlled by the app owner.

We asked a simple question:

> *“What would it look like if agents had their own programmable money,  
> and had to coordinate over a shared budget, just like a real team?”*

MNEE — a USD-backed, ERC-20 stablecoin — is a perfect candidate for this:

- **Permissionless**: any piece of code with a private key can participate.
- **Programmable**: smart contracts & policies can govern spending.
- **Micro-payments**: tiny payments for data, compute, and tools become viable.

MNEE Nexus is our answer: a **shared MNEE treasury + policy engine + agent router**, powering an internal economy of AI agents and paid service providers.

---

## What It Does

At a high level:

> **Agents don’t “know everything” — they “buy capabilities” with MNEE.**

### Core Flow

1. A user types a natural language request into the chat UI.
2. The **Omni-Agent** (LLM + tools) translates the request into calls to tools/services.
3. Before any tool runs, a **Payment Wrapper**:
   - Checks policy and budgets.
   - Calls the on-chain `PaymentRouter` to pay the appropriate provider using MNEE.
4. The service provider validates the payment (by reading `PaymentExecuted` events).
5. The provider executes the service (image generation, data query, batch compute, logging, etc.).
6. The agent returns a result to the user, while the UI shows **real-time MNEE outflows**.

---

## Key Features

### 1. Shared MNEE Treasury for Multiple Agents

- A single treasury (on Ethereum) funds **multiple agents**:
  - `user-agent` – interactive user-facing tasks.
  - `batch-agent` – heavy batch compute jobs.
  - `ops-agent` – logging, archiving, and observability.
- Each agent has:
  - Daily budget
  - Per-call cap
  - Priority (HIGH / MEDIUM / LOW)

### 2. Four Core Service Providers (MVP)

We model four **archetypes of paid services**:

1. **ImageGen Provider**
   - Generates avatars / thumbnails / images.
   - Example: “Generate a cyberpunk Twitter avatar.”
   - Billed per call, e.g. `1.0 MNEE / image`.

2. **PriceOracle Provider**
   - Returns ETH/MNEE prices or other market data.
   - Used for: “How much ETH is 100 MNEE worth?”
   - Billed per query, e.g. `0.05 MNEE / query`.

3. **Batch Compute Provider**
   - Accepts heavy jobs (batch generation, analysis, etc.).
   - Jobs may take seconds/minutes → modeled as queued compute.
   - Billed per job or per compute unit, e.g. `3.0 MNEE / job`.

4. **Log Archive Provider**
   - Stores detailed activity logs and execution traces.
   - Enables auditing / compliance / post-mortems.
   - Billed per log entry or MB, e.g. `0.01 MNEE / log`.

Each service is integrated through the same **payment + policy interface**, so other APIs can be plugged in later.

---

## How It Uses MNEE

- We use the official MNEE ERC-20 contract on Ethereum:
  - **Contract:** `0x8ccedbAe4916b79da7F3F612EfB2EB93A2bFD6cF`
- The `PaymentRouter` contract:
  - Pulls MNEE from a **treasury address** (which pre-approves the router).
  - Sends MNEE to **service provider addresses**.
  - Emits `PaymentExecuted` events containing:
    - `serviceId`
    - `agentId`
    - `taskId`
    - `amount`
    - `provider`
- Off-chain providers subscribe to these events to verify they were paid before serving requests.

**Why MNEE, not traditional payments?**

- No KYC or credit card required for an agent.
- Permissionless — any agent with a key can participate.
- Fully programmable — payment logic is composable with smart contracts.
- Perfect for **micro-payments** for data, compute, and storage.

---

## How It Solves Real Coordination Problems

The hackathon explicitly cares about:

> “Solves Real Coordination Problems.”

We model three real-world coordination tradeoffs:

### 1. Front-office UX vs Back-office Heavy Compute

- `user-agent` wants to keep the chat snappy using **ImageGen** and **PriceOracle**.
- `batch-agent` wants to launch **expensive BatchCompute jobs**.
- The payment policy enforces:
  - Always reserve a minimum budget for `user-agent` interactive tasks.
  - Reject or downscale large batch jobs that would eat into that reserve.
- In the UI, this appears as:
  - `[POLICY_REJECTED]` logs when batch jobs are denied to protect UX.

### 2. Short-term Features vs Long-term Auditability

- `ops-agent` uses **LogArchive** to store detailed logs.
- When the treasury is healthy:
  - Full logs are stored (high transparency).
- When funds run low:
  - Policy automatically **downgrades** LogArchive to summary-only:
    - Fewer details → cheaper but less auditability.
- This is a classic coordination tradeoff:
  - “How much are we willing to pay for future auditability during a budget crunch?”

### 3. Information Cost vs Decision Quality

- PriceOracle queries are paid.
- High-priority agents can query fresh prices more often.
- Low-priority agents may be forced to reuse cached prices.
- The system forces agents to balance:
  - “Spend more MNEE to be more certain,” vs  
  - “Save MNEE and accept imperfect information.”

All of these coordination decisions are:

- **Enforced by policy**, not manually tweaked each time.
- **Logged and visualized** in the front-end “System Log / Policy Console.”

---

## How We Built It

> *Note: adapt this section to match your final stack.*

**Tech stack (planned):**

- **Smart Contracts**
  - Solidity + Hardhat
  - `ServiceRegistry.sol` – stores providers, unit prices, active flags.
  - `PaymentRouter.sol` – routes MNEE payments, emits events.

- **Backend / Orchestration**
  - Python + FastAPI (or Node.js) for APIs.
  - LangChain / LangGraph for the Omni-Agent and tools.
  - Policy Engine in Python:
    - Reads budgets & priorities.
    - Decides allow / deny / downgrade.

- **Frontend**
  - Next.js + React
  - Chat UI + Dashboard:
    - Treasury balance
    - Real-time transaction stream
    - Per-agent and per-service spending charts
    - System Log for policy decisions

- **Off-chain Service Providers**
  - Implemented as simple HTTP services:
    - `ImageGen` – returns pre-configured URLs (mock) or calls a real image API.
    - `PriceOracle` – returns mock or real price data.
    - `BatchCompute` – queues fake jobs and returns results after a delay.
    - `LogArchive` – stores log entries in a DB or local file.

---

## Challenges We Ran Into

- **Designing a generic payment interface**  
  We had to keep contracts minimal while still expressive enough to support very different service types (compute, data, storage).

- **Making coordination visible**  
  Coordination is usually “invisible” — just numbers in a database.  
  We had to surface it through:
  - A dedicated policy log.
  - Clear visual grouping of spending per agent and service.

- **Balancing realism vs hackathon scope**  
  Fully integrating real image models and production-grade data APIs would explode scope.  
  Our approach:
  - Keep **on-chain settlement real**.
  - Allow **off-chain providers to be mock/partial** in the MVP.

---

## Accomplishments That We’re Proud Of

- Built a **unified payment & policy layer** for heterogeneous AI tools.
- Demonstrated four archetypal service providers that cover:
  - Content generation
  - Market data
  - Compute
  - Governance / audit
- Turned MNEE into the **native currency of an internal agent economy**, rather than a simple “checkout coin.”

---

## What We Learned

- Coordination is **not** just governance tokens and voting;  
  it’s also about budgets, priorities, and access to compute/data/storage.
- Giving agents real money (MNEE) forces us to treat them like economic actors —  
  and that completely changes how we design tools and APIs.
- A thin, composable on-chain layer + a rich off-chain policy engine is a powerful pattern.

---

## What’s Next

- Turn the current code into a **reusable SDK**:
  - A Python/TypeScript package that wraps tools with MNEE payments by default.
- Add more provider types:
  - RAG / vector search
  - Risk scoring
  - Notification / alerting providers
- Explore **multi-tenant treasuries**:
  - Different teams or DAOs running their own policies on top of the same MNEE infrastructure.

---

## How to Run the Demo (High-level)

> See the GitHub README for full instructions.

1. Deploy `ServiceRegistry` and `PaymentRouter` with Hardhat.
2. Fund the treasury address with MNEE and approve the router.
3. Start the backend (policy engine + providers) with Docker or `docker-compose`.
4. Start the Next.js frontend.
5. Open the web UI:
   - Chat with the Omni-Agent.
   - Watch MNEE flows in real time.
   - Trigger coordination conflicts (e.g. large batch jobs with low remaining budget) and observe policy decisions.
