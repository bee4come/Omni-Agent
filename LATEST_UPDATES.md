# MNEE Agent Cost & Billing Hub - Latest Updates

**Last Updated:** November 25, 2025

This document summarizes the major architectural and feature updates transforming the "Omni-Agent" project into a production-grade **MNEE Agent Cost & Billing Hub**.

The system solves the critical coordination problem of **managing budgets, enforcing policies, and auditing expenses** for teams running multiple autonomous AI agents.

---

## 1. Core Value Proposition: "The Financial OS for AI Agents"

Instead of a simple chatbot that pays for tools, the system now functions as a centralized **Cost Center**:

*   **Unified Treasury**: All agents draw MNEE stablecoin from a single, managed treasury.
*   **Project-Based Budgeting**: Agents are grouped into "Projects" (e.g., "Marketing", "Data Analysis") with strict daily spending caps.
*   **AI Auditor (The Guardian)**: Every transaction is reviewed by an LLM-powered auditor that checks context, history, and alignment with user goals before approval.
*   **Live Command Center**: A real-time dashboard visualizing the decision-making process and financial flows.

---

## 2. Key Features Implemented

### A. Intelligent AI Guardian (CFO)
*   **What it is**: A dedicated LangGraph node (`Guardian`) that acts as a gatekeeper.
*   **How it works**:
    *   Before any tool execution, it receives the User's Goal, the Proposed Plan, and the **Last 10 Transactions**.
    *   It uses a large language model (Gemini 2.5 Flash / GPT-4o-mini) to reason about the request.
    *   **Checklist**:
        *   Is this relevant to the goal?
        *   Is the cost efficient?
        *   Is this a duplicate/spam request (Burst detection)?
    *   **Output**: Returns a `Risk Score (0-10)` and a detailed `Reasoning` string.
*   **Benefit**: Prevents runaway agent spending and "hallucinated" purchases.

### B. Project & Agent Hierarchies
*   **New Data Models**:
    *   `ProjectPolicy`: Sets global budgets and service allow/deny lists for a group of agents.
    *   `AgentPolicy`: Sets individual daily limits and priorities (HIGH/NORMAL/LOW).
*   **Enforcement**: The `PolicyEngine` now strictly enforces:
    *   `Service Whitelisting`: Can this project use "ImageGen"?
    *   `Single Transaction Limit`: Cap individual API calls (e.g., max 5 MNEE).
    *   `Daily Budget`: Hard stop when the budget runs dry.

### C. Provider-Agnostic LLM Layer
*   **Flexibility**: The system no longer hardcodes a specific model.
*   **Utility**: `backend/agents/utils.py` dynamically selects the best available provider:
    1.  **OpenAI** (`gpt-4o-mini`)
    2.  **Google** (`gemini-2.5-flash`)
    3.  **AWS Bedrock** (`claude-haiku-4.5`)
*   **Benefit**: Ensuring the "Brain" is always online and cost-optimized.

### D. Live Command Center (Frontend)
*   **Visual Graph**: A real-time visualization of the Agent's "Thought Process" (`Planner` → `Guardian` → `Executor`).
*   **Audit Log**: A transparent ledger showing every Policy Decision (ALLOW/DENY) with color-coded risk scores.
*   **Streaming Experience**: The UI simulates the asynchronous agent workflow, giving users immediate feedback on what the AI is thinking and buying.

---

## 3. Technical Architecture

### Backend (Python + LangGraph)
*   **Orchestrator**: `OmniAgent` (StateGraph) manages the lifecycle.
*   **Nodes**:
    *   `Planner`: Decomposes goals into steps and delegates to specialist agents (e.g., `startup-designer`).
    *   `Guardian`: Performs AI audit and Policy checks.
    *   `Executor`: Executes tools via `PaidToolWrapper`.
*   **Services**:
    *   `Guardian Service`: Isolated, secure key management for MNEE transactions.
    *   `Policy Engine`: Rule-based budget enforcement.

### Frontend (Next.js + Tailwind)
*   **Components**:
    *   `LiveGraph`: Visualizes the node execution flow.
    *   `AuditLog`: Displays financial compliance records.
    *   `ChatInterface`: Interactive terminal for issuing commands.

### Blockchain (Ethereum / Hardhat)
*   **Contracts**:
    *   `MNEEPaymentRouter`: Routes payments and emits verified events.
    *   `MNEEServiceRegistry`: On-chain registry of approved vendors.
*   **Integration**: Uses a local Hardhat node for zero-cost, high-speed testing of the full payment lifecycle.

---

## 4. How to Demo

1.  **Start the System**:
    ```bash
    ./start_all.sh restart
    ```
2.  **Open Dashboard**:
    Go to `http://localhost:3000`.
3.  **Run a Scenario**:
    *   Type: *"Generate a logo for our new AI startup."*
    *   **Watch**:
        1.  **Planner** delegates to `startup-designer`.
        2.  **Guardian** audits the request (Green Shield: "Risk Score 0/10").
        3.  **Executor** pays 1.0 MNEE to `ImageGen`.
        4.  **Audit Log** updates with the transaction details.

---

## 5. Future Roadmap

*   **Multi-Tenant Treasury**: Support multiple distinct wallets for different organizations.
*   **On-Chain Governance**: Allow DAO voting to update Project Budgets.
*   **Invoice Settlement**: Enable Agent-to-Agent invoicing with net-30 settlement terms using MNEE streams.
