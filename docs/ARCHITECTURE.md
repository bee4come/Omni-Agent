# MNEE Agent Cost & Billing Hub - Architecture

## System Overview

```
+------------------------------------------------------------------------------------+
|                              MNEE Agent Payment Orchestration                       |
+------------------------------------------------------------------------------------+

                                  +------------------+
                                  |    Frontend      |
                                  |   (Next.js)      |
                                  |   Port: 3000     |
                                  +--------+---------+
                                           |
                                           | HTTP/WebSocket
                                           v
+--------------------------------------------------------------------------------------+
|                                    Backend Layer                                      |
|                                                                                       |
|  +----------------+     +------------------+     +------------------+                 |
|  |   FastAPI      |     |   LangGraph      |     |   Policy Engine  |                |
|  |   Port: 8000   |<--->|   Orchestrator   |<--->|   (Budget/Rules) |                |
|  +-------+--------+     +--------+---------+     +------------------+                |
|          |                       |                                                    |
|          v                       v                                                    |
|  +----------------+     +------------------+     +------------------+                 |
|  |   A2A Client   |     |   Payment Client |     |   System Logger  |                |
|  | (Agent Wallets)|     |  (Calls Guardian)|     |   (Audit Trail)  |                |
|  +-------+--------+     +--------+---------+     +------------------+                |
|          |                       |                                                    |
+----------|-----------------------|----------------------------------------------------+
           |                       |
           |                       v
           |              +------------------+
           |              |   Guardian       |
           |              |   Service        |
           |              |   Port: 8100     |
           |              | (ONLY key holder)|
           |              +--------+---------+
           |                       |
           v                       v
+--------------------------------------------------------------------------------------+
|                              Smart Contract Layer                                     |
|                              (Hardhat Fork / Ethereum)                                |
|                                                                                       |
|  +------------------+   +------------------+   +------------------+   +-------------+ |
|  | MNEEAgentWallet  |   | MNEEPaymentRouter|   | MNEEEscrow       |   | MNEE Token  | |
|  | (A2A Payments)   |   | (Service Payments)|  | (Trustless)      |   | (ERC-20)    | |
|  +------------------+   +------------------+   +------------------+   +-------------+ |
|                                                                                       |
+--------------------------------------------------------------------------------------+
                                           |
                                           v
+--------------------------------------------------------------------------------------+
|                              Service Provider Layer                                   |
|                                                                                       |
|  +----------------+   +----------------+   +----------------+   +----------------+    |
|  |   ImageGen     |   |  PriceOracle   |   | BatchCompute   |   |  LogArchive    |   |
|  |   Port: 8001   |   |   Port: 8002   |   |   Port: 8003   |   |   Port: 8004   |   |
|  |   1.0 MNEE     |   |   0.05 MNEE    |   |   3.0 MNEE     |   |   0.01 MNEE    |   |
|  +----------------+   +----------------+   +----------------+   +----------------+    |
|                                                                                       |
+--------------------------------------------------------------------------------------+
```

## Core Data Flow: Escrow-Verify-Release Protocol

```
User Request: "Generate a marketing image"
        |
        v
+-------+--------+
|    Planner     |  Analyzes request, creates execution plan
+-------+--------+  [Estimated cost: 1.0 MNEE]
        |
        v
+-------+--------+
|    Guardian    |  Risk assessment, budget check
+-------+--------+  [Risk score: 2/10, Budget OK]
        |
        v
+-------+--------+
|  Escrow Lock   |  Locks funds in smart contract
+-------+--------+  [1.0 MNEE locked in MNEEEscrow]
        |
        v
+-------+--------+
|    Executor    |  Calls service provider, pays via Guardian
+-------+--------+  [ImageGen API call successful]
        |
        v
+-------+--------+
|    Verifier    |  Validates output quality
+-------+--------+  [Score: 92/100, PASSED]
        |
        v
+-------+--------+
| Escrow Release |  Releases funds to merchant
+-------+--------+  [0.99 MNEE to provider, 0.01 MNEE fee]
        |
        v
+-------+--------+
|   Summarizer   |  Generates user response
+-------+--------+  [Image URL + cost breakdown]
```

## Agent-to-Agent (A2A) Commerce Flow

```
+----------------+          +----------------+          +----------------+
|  Customer      |          |   Merchant     |          |   Verifier     |
|  Agent         |          |   Agent        |          |   Agent        |
+-------+--------+          +-------+--------+          +-------+--------+
        |                           |                           |
        | 1. Create Escrow          |                           |
        |  (Lock 10 MNEE)           |                           |
        +-------------------------->|                           |
        |                           |                           |
        |         2. Work Submitted |                           |
        |<--------------------------+                           |
        |           (IPFS proof)    |                           |
        |                           |                           |
        | 3. Request Verification   |                           |
        +------------------------------------------------->     |
        |                           |                           |
        |                           |    4. Score: 85/100       |
        |<-------------------------------------------------+    |
        |                           |                           |
        | 5. Release Funds          |                           |
        +-------------------------->|                           |
        |    (9.9 MNEE to merchant) |                           |
        |                           |                           |
```

## Security Architecture

```
+---------------------------+
|   Application Layer       |
|  (Backend, Frontend)      |
|                           |
|  - Never holds keys       |
|  - Calls Guardian API     |
+------------+--------------+
             |
             | HTTP (localhost only)
             v
+------------+--------------+
|   Guardian Service        |
|   (Port 8100)             |
|                           |
|  - ONLY key holder        |
|  - Signs transactions     |
|  - Audit logging          |
|  - Rate limiting          |
+------------+--------------+
             |
             | Signed TX
             v
+------------+--------------+
|   Ethereum (Hardhat Fork) |
|                           |
|  - MNEE ERC-20 transfers  |
|  - Event emission         |
|  - Immutable audit trail  |
+---------------------------+
```

## Policy Engine Decision Flow

```
                     +------------------+
                     | Payment Request  |
                     +--------+---------+
                              |
                              v
                     +------------------+
                     | Check Agent      |
                     | Registration     |
                     +--------+---------+
                              |
              +---------------+---------------+
              |                               |
              v                               v
     +--------+--------+             +--------+--------+
     | Agent Exists    |             | Agent Unknown   |
     +--------+--------+             +--------+--------+
              |                               |
              v                               v
     +------------------+            +------------------+
     | Check Daily      |            |     DENY         |
     | Budget           |            +------------------+
     +--------+---------+
              |
     +--------+--------+--------+
     |                 |        |
     v                 v        v
+----+----+      +-----+-----+  +--------+
| Within  |      | 80-100%   |  | Over   |
| Budget  |      | of limit  |  | Limit  |
+---------+      +-----------+  +--------+
     |                |              |
     v                v              v
+----+----+      +----+----+    +----+----+
| ALLOW   |      |DOWNGRADE|    |  DENY   |
+---------+      +---------+    +---------+
```

## Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| Frontend | Next.js 14, React 18, TailwindCSS | Dashboard UI |
| Backend | FastAPI, Python 3.10+ | API & Orchestration |
| Agent Framework | LangChain, LangGraph | AI Agent workflow |
| Blockchain | Hardhat, Solidity 0.8.24 | Smart contracts |
| Token | MNEE ERC-20 | Stablecoin payments |
| Key Management | Guardian Service | Isolated signing |

## Port Reference

| Port | Service | Description |
|------|---------|-------------|
| 3000 | Frontend | Next.js dashboard |
| 8000 | Backend | FastAPI main API |
| 8100 | Guardian | Secure key management |
| 8001 | ImageGen | Image generation provider |
| 8002 | PriceOracle | Price data provider |
| 8003 | BatchCompute | Batch processing provider |
| 8004 | LogArchive | Log storage provider |
| 8545 | Hardhat | Ethereum RPC node |

## Hackathon Track Alignment

### AI & Agent Payments
- Multi-agent budget coordination
- Autonomous service payments
- A2A commerce (agents hiring agents)

### Financial Automation
- Programmable escrow (Escrow-Verify-Release)
- Automated policy enforcement
- Real-time treasury management

### Solves Coordination Problems
- Shared budgeting across agent teams
- Treasury transparency and audit trails
- Automated governance via policy engine
