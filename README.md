# 🤖 MNEE Nexus / Omni-Agent

**Programmable Payment Orchestrator for AI Agents, powered by the MNEE stablecoin.**

> **📖 READ THIS FIRST:**  
> See [**FINAL_PROJECT_OVERVIEW.md**](FINAL_PROJECT_OVERVIEW.md) for the complete explanation of:
> 1. The "Why" (Safety, Anti-Scam, Auditability)
> 2. The Architecture (Layers 1-4)
> 3. The new **A2A (Agent-to-Agent) Commerce Rail**

> Let multiple AI agents share one MNEE treasury,  
> pay different service providers on a pay-per-task basis,  
> and enforce budgets, priorities, and policies across the whole system.

[![MNEE Contract](https://img.shields.io/badge/MNEE-0x8cce...D6cF-blue)](https://etherscan.io/address/0x8ccedbAe4916b79da7F3F612EfB2EB93A2bFD6cF)
[![Built for MNEE Hackathon](https://img.shields.io/badge/MNEE%20Hackathon-2026-green)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 💰 MNEE Integration

**Real Contract, Zero Cost Testing**

This project is built on the official **MNEE USD Stablecoin** contract:
```
0x8ccedbAe4916b79da7F3F612EfB2EB93A2bFD6cF (Ethereum Mainnet)
```

We use **Hardhat's mainnet fork** for development:
- ✅ All interactions are with the **real MNEE contract**
- ✅ Full ERC-20 functionality (transfers, approvals, events)
- ✅ **No real funds needed** - runs on localhost fork
- ✅ Instant confirmations for rapid testing
- ✅ **Production-ready** - switch to mainnet by changing RPC URL

### Why Fork?

This approach perfectly balances hackathon requirements with practicality:
1. **Compliant**: Built on the actual MNEE contract (not a mock)
2. **Functional**: All smart contract logic works identically to mainnet
3. **Cost-effective**: No real ETH or MNEE required
4. **Reproducible**: Anyone can run the same setup locally

See [HARDHAT_FORK_GUIDE.md](HARDHAT_FORK_GUIDE.md) for setup instructions.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Core Components](#core-components)
  - [1. Smart Contracts](#1-smart-contracts)
  - [2. Backend & Orchestration](#2-backend--orchestration)
  - [3. Service Providers](#3-service-providers)
  - [4. Frontend](#4-frontend)
- [Repository Structure](#repository-structure)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Clone & Install](#clone--install)
  - [Environment Variables](#environment-variables)
  - [Running the Stack](#running-the-stack)
- [Usage](#usage)
- [Configuration](#configuration)
  - [Agent Budgets & Priorities](#agent-budgets--priorities)
  - [Service Registry & Pricing](#service-registry--pricing)
- [Development Guide](#development-guide)
- [Limitations](#limitations)
- [Roadmap](#roadmap)
- [License](#license)

---

## Overview

**MNEE Nexus / Omni-Agent** is an experimental agent economy built around the MNEE USD-backed stablecoin on Ethereum.

Instead of “baking APIs into the app and paying with a hidden credit card”, we:

- Turn tools and APIs into **paid service providers**.
- Settle all usage with **MNEE** via smart contracts.
- Let a pool of **AI agents share a single MNEE treasury**.
- Enforce **policies, budgets, and priorities** off-chain.

MVP includes four core provider types:

1. `ImageGen` – image generation services (e.g. avatars, thumbnails).
2. `PriceOracle` – price / market data queries.
3. `BatchCompute` – heavy, asynchronous compute jobs.
4. `LogArchive` – log storage & auditability.

---

## Architecture

> **Note:** Diagrams omitted here — add your own PNG/SVG in `/docs/diagram.png` and link it.

High-level architecture:

- **Smart Contracts (Ethereum / MNEE)**
  - `ServiceRegistry` – stores providers, unit prices, and activity flags.
  - `PaymentRouter` – routes MNEE payments from a treasury to providers and emits `PaymentExecuted` events.

- **Backend / Orchestration**
  - Policy Engine:
    - Maintains budgets per agent and per service.
    - Decides allow / deny / downgrade requests.
  - Omni-Agent:
    - LLM-based agent (LangChain / LangGraph).
    - Uses tools wrapped with payment logic.

- **Service Providers (Off-chain)**
  - HTTP services implementing:
    - `/image/generate`
    - `/price/current`
    - `/batch/submit`, `/batch/status`
    - `/logs/archive`
  - Each provider:
    - Verifies payment by reading on-chain events.
    - Executes the corresponding task (mock or real).

- **Frontend (Next.js)**
  - Chat UI with the Omni-Agent.
  - Treasury & payments dashboard.
  - Policy & configuration UI.
  - System Log view for policy decisions.

---

## Core Components

### 1. Smart Contracts

Located in: `contracts/`

- `MNEEServiceRegistry.sol`
  - Registers services by `serviceId` (e.g., `IMAGE_GEN`, `PRICE_ORACLE`).
  - Stores:
    - `provider` (address)
    - `unitPrice` (uint256, in MNEE smallest units)
    - `active` (bool)

- `MNEEPaymentRouter.sol`
  - Pulls MNEE from a **treasury** address using `transferFrom`.
  - Sends MNEE to **provider** addresses.
  - Emits:

    ```solidity
    event PaymentExecuted(
        bytes32 indexed paymentId,
        address indexed payer,
        address indexed provider,
        bytes32 serviceId,
        string agentId,
        string taskId,
        uint256 amount,
        uint256 quantity,
        uint256 timestamp
    );
    ```

> **Note:** The actual MNEE token is deployed at  
> `0x8ccedbAe4916b79da7F3F612EfB2EB93A2bFD6cF` on Ethereum.

### 2. Backend & Orchestration

Located in: `backend/`

- `backend/app/main.py` – FastAPI / Express entrypoint.
- `backend/agents/omni_agent.py` – Omni-Agent using LangChain/LLM.
- `backend/agents/tools/` – Tool implementations (ImageGen, PriceOracle, BatchCompute, LogArchive).
- `backend/policy/engine.py` – Payment policy engine:
  - Reads JSON/YAML configs.
  - Returns allow/deny/downgrade decisions.
- `backend/payment/client.py` – On-chain payment client (web3.py or ethers.js).

**Key pattern:**

- Every tool is wrapped by a **PaidToolWrapper** that:
  - Calls Policy Engine → decision.
  - Calls PaymentRouter → payment.
  - Calls provider → execution.
  - Records usage.

### 3. Service Providers

Located in: `providers/`

Example subfolders:

- `providers/imagegen/` – mock or real image service.
- `providers/price_oracle/` – mock or real price feed service.
- `providers/batch_compute/` – simple job queue + status check.
- `providers/log_archive/` – store logs in DB / file.

Each provider:

1. Receives HTTP requests from the backend (with `taskId`, `serviceId`, `paymentId`).
2. Optionally verifies the on-chain `PaymentExecuted` event.
3. Returns a JSON response (URL, data, job status, etc.).

### 4. Frontend

Located in: `frontend/`

- `frontend/pages/index.tsx` – main chat + dashboard page.
- `frontend/components/Chat.tsx` – chat UI with the Omni-Agent.
- `frontend/components/TreasuryPanel.tsx` – treasury balance, spending per agent/service.
- `frontend/components/TransactionStream.tsx` – real-time payments list.
- `frontend/components/PolicyLog.tsx` – System Log for policy decisions.
- `frontend/components/ConfigPanel.tsx` – budgets & pricing configuration.

---

## Repository Structure

Example structure (adapt to your actual layout):

```bash
.
├── contracts/
│   ├── MNEEServiceRegistry.sol
│   ├── MNEEPaymentRouter.sol
│   └── ...
├── backend/
│   ├── app/
│   │   └── main.py
│   ├── agents/
│   │   ├── omni_agent.py
│   │   └── tools/
│   ├── policy/
│   │   └── engine.py
│   └── payment/
│       └── client.py
├── providers/
│   ├── imagegen/
│   ├── price_oracle/
│   ├── batch_compute/
│   └── log_archive/
├── frontend/
│   ├── pages/
│   ├── components/
│   └── ...
├── scripts/
│   ├── deploy_contracts.ts
│   └── seed_services.ts
├── config/
│   ├── agents.yaml
│   └── services.yaml
└── README.md
````

---

## 🚀 Quick Start (5 Minutes)

### Option 1: Automated Startup (Recommended)

```bash
# 1. Validate configuration
python scripts/validate_config.py

# 2. Start all services (Hardhat + Contracts + Providers + Backend)
chmod +x start_all.sh
./start_all.sh

# 3. Check status
./start_all.sh status

# 4. View logs
./start_all.sh logs backend
```

### Option 2: Docker Compose

```bash
# Configure environment
cp backend/.env.example backend/.env
# Edit backend/.env with your settings

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f backend
```

### Option 3: Manual Setup (Advanced)

See detailed instructions below in the "Getting Started" section.

---

## Getting Started

### Prerequisites

* **Node.js** >= 18
* **Python** 3.10+
* **npm** / yarn / pnpm
* **curl** (for health checks)
* **Docker** (optional, for containerized deployment)
* **Ethereum RPC** endpoint (testnet or local Hardhat node)
* **MNEE tokens** on the chosen network (or use MockMNEE for testing)

### Clone & Install

```bash
git clone https://github.com/<your-org>/mnee-nexus-omni-agent.git
cd mnee-nexus-omni-agent

# Install contracts toolchain
cd contracts
npm install
cd ..

# Install backend
cd backend
pip install -r requirements.txt
cd ..

# Install frontend
cd frontend
npm install
cd ..
```

### Environment Variables

Create `.env` files for each part.

**Example `backend/.env`:**

```bash
ETH_RPC_URL=<your_ethereum_rpc_url>
MNEE_TOKEN_ADDRESS=0x8ccedbAe4916b79da7F3F612EfB2EB93A2bFD6cF
PAYMENT_ROUTER_ADDRESS=<deployed_payment_router_address>
TREASURY_PRIVATE_KEY=<private_key_for_treasury>
POLICY_CONFIG_PATH=./config/agents.yaml
SERVICE_CONFIG_PATH=./config/services.yaml
LLM_API_KEY=<your_llm_key>
```

**Example `frontend/.env.local`:**

```bash
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000
NEXT_PUBLIC_ETH_EXPLORER_BASE=https://etherscan.io
```

### Running the Stack

> Adjust commands according to your actual tooling.

1. **Start a local Ethereum node (optional)**

```bash
cd contracts
npx hardhat node
```

2. **Deploy contracts**

```bash
cd contracts
npx hardhat run scripts/deploy_contracts.ts --network localhost
npx hardhat run scripts/seed_services.ts --network localhost
```

3. **Run backend**

```bash
cd backend
uvicorn app.main:app --reload
```

4. **Run providers** (if separate processes)

```bash
cd providers/imagegen
python main.py

cd providers/price_oracle
python main.py

# etc...
```

5. **Run frontend**

```bash
cd frontend
npm run dev
```

Then open: `http://localhost:3000`

---

## Usage

1. Open the web UI.
2. Use the chat box to send requests, such as:

   * “Generate a cyberpunk avatar for my profile.”
   * “What is the current ETH price? How much ETH is 100 MNEE?”
   * “Launch a batch job to process 100 synthetic tasks.”
3. Observe:

   * Real-time **MNEE payments** in the Transaction Stream.
   * Budget usage per Agent and per Service.
   * Policy decisions in the System Log:

     * rejections
     * downgrades (e.g. turning full log archive into summary-only).

---

## Configuration

### Agent Budgets & Priorities

Example `config/agents.yaml`:

```yaml
agents:
  - id: "user-agent"
    priority: "HIGH"
    dailyBudget: 100.0
    maxPerCall: 10.0

  - id: "batch-agent"
    priority: "LOW"
    dailyBudget: 50.0
    maxPerCall: 20.0

  - id: "ops-agent"
    priority: "MEDIUM"
    dailyBudget: 30.0
    maxPerCall: 5.0
```

### Service Registry & Pricing

Example `config/services.yaml`:

```yaml
services:
  - id: "IMAGE_GEN_PREMIUM"
    unitPrice: 1.0
    providerAddress: "<image_provider_address>"
    active: true

  - id: "PRICE_ORACLE"
    unitPrice: 0.05
    providerAddress: "<oracle_provider_address>"
    active: true

  - id: "BATCH_COMPUTE"
    unitPrice: 3.0
    providerAddress: "<batch_provider_address>"
    active: true

  - id: "LOG_ARCHIVE"
    unitPrice: 0.01
    providerAddress: "<log_provider_address>"
    active: true
```

---

## Development Guide

* To add a new service provider:

  1. Register it on-chain via `ServiceRegistry`.
  2. Add its pricing and provider address in `services.yaml`.
  3. Implement a provider HTTP service.
  4. Implement a corresponding tool and PaidToolWrapper binding.

* To add a new agent:

  1. Declare its config in `agents.yaml`.
  2. Add any specific tools in `backend/agents/tools/`.
  3. Optionally give it a custom prompt or behavior in the Omni-Agent.

---

## Limitations

* Currently uses mock or simplified providers for:

  * Image generation
  * Price data
  * Batch compute
  * Log storage
* Uses a single shared treasury; multi-tenant treasuries are future work.
* No production-grade security audit yet.

---

## Roadmap

* [ ] Package the payment + policy layer as a reusable SDK.
* [ ] Integrate real image and data APIs.
* [ ] Add more provider types (RAG, notification, risk scoring).
* [ ] Introduce multi-tenant treasuries and per-tenant policies.
* [ ] Hardening, testing, and security review.

---

## License

This project is open source under the **MIT License**.
See [`LICENSE`](./LICENSE) for details.
