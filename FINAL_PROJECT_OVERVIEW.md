# Omni-Agent: A2A MNEE Payment Infrastructure

## 1. Understanding the Core Problem
**In short:** When multiple AI Agents share a single MNEE wallet/treasury, **who has the authority to pay whom, under what conditions, and for which specific task?**

This breaks down into three critical pillars:

1.  **Safety (Anti-Stupidity):**
    *   Prevents Agents from draining funds due to prompt injection, hallucinations, or phishing.
    *   Every payment must pass a strict **Policy + Risk Engine** check (Budget limits, frequency, approved recipients) before execution.

2.  **Verification (Anti-Scam):**
    *   Ensures a payment is cryptographically bound to a specific service request.
    *   Uses `serviceCallHash` attached to the transaction to prove: "This payment was exactly for this task, and this result is the response to that payment."

3.  **Auditability:**
    *   Human operators must be able to reconstruct the "Why" behind every transaction.
    *   Tracks: Which Agent? How much? For what service? Was it Flagged/Downgraded? What was the Risk Score?

## 2. Implementation Strategy

### Layer 1: Settlement (The "Bank")
*   **Token:** MNEE (UTXO-based Stablecoin).
*   **SDK:** `@mnee/ts-sdk` (Running via Node.js Bridge).
*   **Treasury:** A shared HD Wallet controlled by the Orchestrator.

### Layer 2: Transfer Logic (The "Rails")
*   **Direct P2P Transfers:** Agents sign and broadcast transactions directly to Provider addresses using the SDK.
*   **Service Registry:** Config-based mapping of `serviceId` to `providerAddress`.
*   **MNEE SDK:** Handles UTXO selection, transaction building, and broadcasting.

### Layer 3: Agent Architecture (The "Brain")
*   **`PolicyEngine`:**
    *   Enforces per-agent budgets (`dailyBudget`), per-service limits (`maxDailySpending`), and global risk rules.
    *   Decisions: `ALLOW`, `DOWNGRADE`, `DENY`.
*   **`PaymentClient`:**
    *   Wraps the MNEE SDK.
    *   Handles the crypto complexity: Generates `serviceCallHash`, interacts with the SDK, and logs usage.
*   **`PaidToolWrapper`:**
    *   The standard interface for LangGraph tools. It wraps any API call with the "Check Policy -> Pay -> Call" logic.

### Layer 4: Observability (The "Eyes")
*   **Dashboard & Policy Console:**
    *   Real-time view of Treasury balance.
    *   Live logs of Policy decisions (Accepted vs. Rejected) and Risk assessments.
*   **Receipts:**
    *   Cryptographic proof of purchase (`ticketId`, `txid`) linked to the off-chain service result.

---

## 3. The A2A Extension: Agent-to-Agent Commerce
We have extended the system from "Agent paying a static API" to **"Customer Agent negotiating with a Merchant Agent"**.

### The Workflow
1.  **Customer Agent** (representing the user) asks **Merchant Agent** for a quote.
2.  **Merchant Agent** computes price and returns a signed `QUOTE`.
3.  **Customer Agent** runs the Quote through the **Policy Engine**.
4.  **Customer Agent** pays via **MNEE SDK**, generating a `ticketId` (TXID).
5.  **Customer Agent** sends the `Payment Receipt` to the Merchant Agent.
6.  **Merchant Agent** validates the transaction status and delivers the goods (Service Result).

This transforms the project from a simple "AI Wallet" into a **Commerce Rail for Autonomous Agents**.