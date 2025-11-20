# Anti-Spoofing & Risk Control Implementation

## Overview
This document describes the enhanced anti-spoofing, credit, and risk control features implemented in the MNEE Nexus / Omni-Agent system.

## Key Components

### 1. ServiceCallHash - Anti-Spoofing Mechanism

**Purpose**: Cryptographically bind on-chain payments to specific off-chain service invocations.

**Flow**:
```
1. Backend computes: serviceCallHash = SHA256(service_id | agent_id | task_id | canonical_payload)
2. Backend calls: PaymentRouter.payForService(..., serviceCallHash)
3. On-chain event emits: PaymentExecuted(..., serviceCallHash, ...)
4. Provider receives: taskId + serviceCallHash in API call
5. Provider can verify: payment corresponds to this exact service call
```

**Implementation**: `PaymentClient.build_service_call_hash()`

### 2. Risk Assessment Engine

**Purpose**: Detect suspicious patterns before executing payments.

**Risk Levels**:
- `RISK_OK`: Normal operation
- `RISK_REVIEW`: Warning, but can proceed (logged for review)
- `RISK_BLOCK`: Denied immediately

**Detection Patterns**:

| Pattern | Trigger | Action |
|---------|---------|--------|
| Burst calls | >5 calls/minute with total >10 MNEE | BLOCK |
| First large call | Low-priority agent, <3 total calls, >5 MNEE | REVIEW |
| Provider failures | >3 recent failures | REVIEW |
| Unusually large call | Single call >20 MNEE | REVIEW |

**Implementation**: `RiskEngine` class in `policy/engine.py`

### 3. Enhanced Policy Decision

**New Decision Model**:
```python
class PolicyDecision:
    action: "ALLOW" | "DENY" | "DOWNGRADE"
    approved_quantity: int
    risk_level: "RISK_OK" | "RISK_REVIEW" | "RISK_BLOCK"
    reason: str
```

**Evaluation Flow**:
```
1. Validate agent + service existence
2. Check access control (allowedAgents/blockedAgents)
3. Run risk assessment
4. Check budget constraints (maxPerCall, dailyBudget)
5. Return combined decision
```

### 4. Service Verification

**isVerified Flag**: Indicates trusted/verified service providers.

**Purpose**:
- UI shows ✅ for verified services, ⚠️ for unverified
- Policy engine can apply stricter rules to unverified providers
- Users can make informed decisions

**Implementation**: 
- Smart contract: `MNEEServiceRegistry.isVerified`
- Backend: `ServiceConfig.isVerified`
- Frontend: Badge display in UI

### 5. Payment Result Structure

**Enhanced PaymentResult**:
```python
PaymentResult(
    success: bool
    payment_id: str
    tx_hash: str
    service_call_hash: str  # NEW: Anti-spoofing hash
    amount: float
    risk_level: str  # NEW: Risk assessment result
    policy_action: str  # NEW: ALLOW/DENY/DOWNGRADE
    error: str
)
```

## Integration Points

### Smart Contracts
- **MNEEServiceRegistry**: `isVerified`, `metadataURI` fields
- **MNEEPaymentRouter**: `serviceCallHash` parameter

### Backend (Python)
- **PolicyEngine**: Unified evaluation with risk assessment
- **PaymentClient**: Computes serviceCallHash, enforces policy
- **PaidToolWrapper**: Anti-spoofing aware tool wrapper
- **OmniAgent**: Uses enhanced components in LangGraph flow

### Service Providers
- **API Changes**: All providers must accept `taskId` and `serviceCallHash`
- **Response**: Providers echo back `serviceCallHash` for verification

### Frontend (Next.js)
- **Config Panel**: Display `isVerified` badges
- **Policy Console**: Show risk levels (RISK_OK, RISK_REVIEW, RISK_BLOCK)
- **Transaction Stream**: Display `serviceCallHash` (truncated)
- **Receipt Detail**: Full anti-spoofing verification view

## Testing Scenarios

### Scenario 1: Normal Flow (RISK_OK)
```
User: "Generate avatar"
→ Risk: RISK_OK
→ Policy: ALLOW
→ Payment: Success with serviceCallHash
→ Provider: Receives taskId + serviceCallHash
→ Result: Image URL + receipt
```

### Scenario 2: Risk Review (Large First Call)
```
Batch-Agent: First call, 15 MNEE
→ Risk: RISK_REVIEW (first large call from low-priority agent)
→ Policy: ALLOW (but logged for review)
→ Payment: Success
→ UI: Shows RISK_REVIEW warning in policy console
```

### Scenario 3: Risk Block (Burst Attack)
```
Agent: 10 calls in 30 seconds, 50 MNEE total
→ Risk: RISK_BLOCK (burst detected)
→ Policy: DENY
→ Payment: Not executed
→ UI: Shows DENY with "Burst detected" reason
```

### Scenario 4: Budget Downgrade
```
User-Agent: Requests 100 units, only 20 MNEE remaining
→ Risk: RISK_OK
→ Policy: DOWNGRADE to 20 units
→ Payment: Success for 20 units
→ Result: Partial fulfillment with explanation
```

## Security Properties

1. **Payment-Call Binding**: `serviceCallHash` ensures payment matches exact service invocation
2. **Replay Protection**: Each `taskId` is unique, preventing replay attacks
3. **Burst Protection**: Rate limiting via risk engine
4. **Budget Isolation**: Per-agent budgets prevent one agent draining treasury
5. **Provider Trust**: `isVerified` flag helps users assess provider credibility

## Future Enhancements

1. **On-chain Verification**: Providers verify `PaymentExecuted` events
2. **Reputation System**: Track provider performance, adjust trust scores
3. **ML-based Risk**: Machine learning for anomaly detection
4. **Multi-signature**: Require multiple approvals for large payments
5. **Escrow**: Hold payment until service delivery confirmed

## Configuration

### agents.yaml
```yaml
agents:
  - id: "user-agent"
    priority: "HIGH"  # Risk engine considers this
    dailyBudget: 100.0
    maxPerCall: 10.0
```

### services.yaml
```yaml
services:
  - id: "IMAGE_GEN_PREMIUM"
    unitPrice: 1.0
    isVerified: true  # NEW: Verification flag
    metadataURI: "ipfs://..."  # NEW: Provider metadata
    maxDailySpending: 50.0  # Optional limit
    allowedAgents: ["user-agent", "ops-agent"]  # Access control
```

## API Changes

### PaymentRouter.payForService
```solidity
function payForService(
    bytes32 serviceId,
    string calldata agentId,
    string calldata taskId,
    uint256 quantity,
    bytes32 serviceCallHash  // NEW parameter
) external returns (bytes32 paymentId);
```

### Provider APIs
```
POST /image/generate
{
  "prompt": "...",
  "taskId": "...",  // NEW: Unique task identifier
  "serviceCallHash": "0x..."  // NEW: Anti-spoofing hash
}
```

## Monitoring & Logging

All policy and risk decisions are logged with:
- Timestamp
- Agent ID
- Service ID
- Action (ALLOW/DENY/DOWNGRADE)
- Risk Level
- Reason
- Amount

Access via `/api/logs` endpoint for frontend Policy Console.
