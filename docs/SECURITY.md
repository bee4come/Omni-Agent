# Guardian Security Architecture

This document describes the security model of MNEE Nexus, focusing on how the Guardian Service provides isolated key management and why this architecture was chosen.

## Overview

MNEE Nexus implements a **defense-in-depth** security model where sensitive cryptographic operations are isolated from the main application layer. The Guardian Service is the cornerstone of this architecture.

```
+------------------+     HTTP Request      +------------------+
|                  | -------------------> |                  |
|   Main Backend   |                      |  Guardian Service |
|   (Port 8000)    | <------------------- |   (Port 8100)     |
|                  |     Signed Result    |                  |
+------------------+                      +------------------+
        |                                          |
        | Policy Check                             | Signs TX
        v                                          v
+------------------+                      +------------------+
|  Policy Engine   |                      |  TREASURY_KEY    |
|  (No key access) |                      |  (Isolated)      |
+------------------+                      +------------------+
```

## Key Isolation Design

### The Problem

In a naive implementation, the private key for the treasury wallet would be accessible to the main backend:

```
# DANGEROUS: Key accessible throughout the application
payment_client.sign_transaction(private_key)  # Key exposed!
```

This creates several risks:
- Memory dump attacks could extract the key
- Logging mistakes could leak the key
- Any vulnerability in the main backend exposes the key
- Multiple code paths have access to sensitive material

### The Solution: Guardian Service

The Guardian Service is the **ONLY** component that holds `TREASURY_PRIVATE_KEY`:

1. **Separate Process**: Guardian runs on port 8100, isolated from the main backend
2. **Minimal API Surface**: Only exposes `/guardian/quote` and `/guardian/pay` endpoints
3. **No Key Export**: The signing key never leaves the Guardian process

```python
# Guardian Service (Port 8100) - ONLY place with key access
class GuardianService:
    def __init__(self):
        self._private_key = os.getenv("TREASURY_PRIVATE_KEY")

    def sign_and_execute(self, payment_request):
        # Key is used here, never exported
        return self.web3.sign_transaction(...)
```

```python
# Payment Client (Port 8000) - NO key access
class PaymentClient:
    async def execute_payment(self, ...):
        # Calls Guardian API instead of signing directly
        return await self.http.post("http://localhost:8100/guardian/pay", ...)
```

## Threat Model

### Threats Mitigated

| Threat | Mitigation |
|--------|------------|
| Main backend compromise | Private key remains in isolated Guardian |
| Memory dump on backend | Key only in Guardian process memory |
| Log leakage | Backend never sees or logs the key |
| SQL injection in backend | Cannot access Guardian's environment |
| Dependency vulnerability | Attack surface limited to Guardian's minimal deps |

### Attack Scenarios

**Scenario 1: Backend RCE**
- Attacker gains code execution on the main backend (port 8000)
- They can call Guardian's `/pay` endpoint
- But they CANNOT extract the private key
- Damage is limited to authorized payment requests

**Scenario 2: Environment Variable Leak**
- If backend logs or exposes environment variables
- `TREASURY_PRIVATE_KEY` is only set in Guardian's environment
- Backend's `.env` does not contain the key

**Scenario 3: Insider Threat**
- Developer with backend code access
- Cannot see or modify Guardian's key handling
- Separation of concerns limits access

## Why This Architecture?

### 1. Principle of Least Privilege

The main backend only needs to:
- Request quotes (cost estimation)
- Request payments (execution)

It does NOT need to:
- Hold private keys
- Sign transactions directly
- Manage wallet state

### 2. Single Point of Failure Isolation

If the main backend fails or is compromised:
- Guardian remains secure
- Key material is not exposed
- Recovery only requires patching the backend

### 3. Bank-Grade Security Pattern

This mirrors how financial institutions operate:
- **Trading Systems** (Backend): Request trades
- **Custody Systems** (Guardian): Hold keys, execute settlements

The pattern is proven in production at scale.

### 4. Audit Trail

Every payment request goes through a single choke point:
- Guardian logs all signing requests
- Easy to audit who requested what payment
- Clear separation in logs between requests and executions

## Security Best Practices

### Production Deployment

For production environments, consider:

1. **Hardware Security Module (HSM)**
   - Guardian could delegate signing to an HSM
   - Key never exists in process memory

2. **Network Isolation**
   - Run Guardian on a separate machine
   - Use firewall rules to limit access

3. **Rate Limiting**
   - Limit requests to Guardian API
   - Prevent budget exhaustion attacks

4. **Multi-Signature**
   - Require multiple Guardian approvals
   - Threshold signatures for high-value transactions

### Current Implementation (Hackathon MVP)

For the hackathon demo:
- Guardian runs on localhost:8100
- Single-signature for simplicity
- Focus on demonstrating the architecture

## API Reference

### Guardian Endpoints

#### `GET /guardian/balance`
Check treasury balance without signing.

#### `POST /guardian/quote`
Pre-check if a payment is possible.
```json
{
  "service_id": "IMAGE_GEN",
  "amount": 1.0,
  "agent_id": "user-agent"
}
```

#### `POST /guardian/pay`
Execute a signed payment.
```json
{
  "service_id": "IMAGE_GEN",
  "amount": 1.0,
  "provider_address": "0x...",
  "agent_id": "user-agent"
}
```

Returns:
```json
{
  "success": true,
  "tx_hash": "0x...",
  "amount": 1.0
}
```

## Summary

The Guardian Service architecture provides:

- **Key Isolation**: Private key only in Guardian process
- **Minimal Attack Surface**: Only `/quote` and `/pay` endpoints
- **Defense in Depth**: Compromise of one component doesn't expose keys
- **Audit Trail**: All transactions go through single choke point
- **Production Ready**: Pattern scales to HSM and multi-sig

This design ensures that even if the main backend is compromised, the treasury's private key remains secure.
