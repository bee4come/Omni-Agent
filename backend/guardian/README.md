# Guardian Service - Secure Key Management Layer

## Overview

Guardian Service is an **isolated key management layer** that serves as the sole holder of `TREASURY_PRIVATE_KEY`. It provides a secure boundary between the main application logic and cryptographic signing operations.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Application Layer                        │
│  ┌──────────────┐      ┌──────────────┐                    │
│  │ Policy Engine│      │ Payment Client│                    │
│  └──────────────┘      └───────┬───────┘                    │
│                                 │ HTTP                       │
└─────────────────────────────────┼──────────────────────────┘
                                  │
                      ┌───────────▼────────────┐
                      │  Guardian Service      │
                      │  (Port 8100)           │
                      │                        │
                      │  ┌──────────────────┐ │
                      │  │ PRIVATE KEY      │ │
                      │  │ (Only here!)     │ │
                      │  └──────────────────┘ │
                      └───────────┬────────────┘
                                  │ Web3
                      ┌───────────▼────────────┐
                      │  MNEE PaymentRouter    │
                      │  (Smart Contract)      │
                      └────────────────────────┘
```

## Why Guardian Service?

### Security Benefits

1. **Isolated Key Storage**: Private key is only accessible to Guardian process
2. **Minimal Attack Surface**: Guardian only exposes 3 endpoints (quote, pay, balance)
3. **TEE-Ready**: Can be migrated to Trusted Execution Environment without changing upper layers
4. **Audit Trail**: All signing operations logged in one place

### MNEE Compliance

Per MNEE official requirements:
- Payments must use **real MNEE token transfers**
- Self-transfers are allowed (treasury to treasury)
- Intermediate contracts are permitted (PaymentRouter)
- Infrastructure-only Agents are acceptable

Guardian ensures all these requirements are met while maintaining security.

## API Endpoints

### POST /guardian/quote

Pre-check if payment is possible without executing it.

**Request:**
```json
{
  "agent_id": "user-agent",
  "service_id": "IMAGE_GEN_PREMIUM",
  "quantity": 1,
  "estimated_unit_price": 1.0
}
```

**Response:**
```json
{
  "can_pay": true,
  "max_quantity": 1,
  "reason": "Guardian checks passed",
  "treasury_balance": 1000.0
}
```

### POST /guardian/pay

Execute actual on-chain payment (requires valid service_call_hash).

**Request:**
```json
{
  "agent_id": "user-agent",
  "service_id": "IMAGE_GEN_PREMIUM",
  "task_id": "task-123",
  "quantity": 1,
  "service_call_hash": "0x1234abcd..."
}
```

**Response:**
```json
{
  "success": true,
  "payment_id": "0xabc123...",
  "tx_hash": "0xdef456...",
  "reason": null
}
```

### GET /guardian/balance

Query Treasury MNEE balance.

**Response:**
```json
{
  "success": true,
  "address": "0x70997970C51812dc3A010C7d01b50e0d17dc79C8",
  "balance_mnee": 995.5,
  "balance_wei": "995500000000000000000"
}
```

## Configuration

### Environment Variables

Add to `backend/.env`:

```bash
# Guardian Service Configuration
GUARDIAN_URL=http://localhost:8100
GUARDIAN_PORT=8100
MNEE_ENV=local

# Treasury Private Key (only Guardian uses this)
TREASURY_PRIVATE_KEY=0x59c6995e998f97a5a0044966f0945389dc9e86dae88c7a8412f4603b6b78690d
```

### Running Guardian

#### Option 1: Via start_all.sh (Recommended)
```bash
./start_all.sh
```

Guardian starts automatically on port 8100.

#### Option 2: Standalone
```bash
cd backend/guardian
./start_guardian.sh
```

#### Option 3: Manual
```bash
cd backend
python -m guardian.service
```

## Integration with Payment Client

The Payment Client has been refactored to **never directly access private keys**.

### Old Flow (Insecure)
```python
# payment/client.py (old)
self.treasury_key = os.getenv("TREASURY_PRIVATE_KEY")
response = self.mnee.pay_for_service(..., private_key=self.treasury_key)
```

### New Flow (Secure)
```python
# payment/client.py (new)
# No private key access
response = httpx.post(f"{GUARDIAN_URL}/guardian/pay", json={...})
```

## Security Considerations

### Current Setup

- Guardian runs as separate process on localhost
- Only communicates via HTTP with Payment Client
- Private key stored in environment variable

### Future Enhancements

1. **TEE Migration**: Move Guardian to SGX/TDX enclave
2. **Hardware Security Module**: Store key in HSM
3. **Multi-Sig**: Require multiple approvals for large payments
4. **Rate Limiting**: Add sophisticated rate limiting at Guardian level
5. **Audit Logging**: Export all signing operations to immutable log

## Troubleshooting

### Guardian fails to start

**Error:** `TREASURY_PRIVATE_KEY must be set for Guardian Service`

**Solution:** Ensure `.env` file has valid private key:
```bash
cd backend
grep TREASURY_PRIVATE_KEY .env
```

### Payment Client can't connect to Guardian

**Error:** `Failed to connect to Guardian: Connection refused`

**Solution:** Check Guardian is running:
```bash
curl http://localhost:8100/
```

Should return:
```json
{"service": "MNEE Guardian", "status": "operational", ...}
```

### Guardian returns "Insufficient treasury balance"

**Check balance:**
```bash
curl http://localhost:8100/guardian/balance
```

**Fund treasury** (on Hardhat fork):
```javascript
// In Hardhat console
await mnee.transfer(treasuryAddress, ethers.parseEther("1000"))
```

## Development Notes

### Adding New Guardian Checks

To add custom validation logic, edit `evaluate_payment_request()` in `service.py`:

```python
def evaluate_payment_request(req: QuoteRequest) -> QuoteResponse:
    # Your custom checks here
    if req.quantity > MY_LIMIT:
        return QuoteResponse(can_pay=False, ...)

    return QuoteResponse(can_pay=True, ...)
```

### Monitoring Guardian Activity

Logs are in `logs/guardian.log`:
```bash
tail -f logs/guardian.log
```

### Testing Without Full Stack

Start Guardian standalone:
```bash
cd backend
python -m guardian.service
```

Test with curl:
```bash
# Quote
curl -X POST http://localhost:8100/guardian/quote \
  -H "Content-Type: application/json" \
  -d '{"agent_id":"test","service_id":"TEST","quantity":1}'

# Balance
curl http://localhost:8100/guardian/balance
```

## Migration Path to Production

### Step 1: Current (Local Development)
- Guardian runs on localhost:8100
- Private key in `.env` file

### Step 2: Container Isolation
- Run Guardian in separate Docker container
- Use Docker secrets for key management
- Internal network only (no external exposure)

### Step 3: TEE Integration
- Migrate Guardian to SGX/TDX enclave
- Attest Guardian before trusting
- Key sealed to enclave

### Step 4: Hardware Security
- Store key in HSM
- Guardian calls HSM for signing
- Never expose key material

## Related Documentation

- Main README: `../../README.md`
- Payment Client: `../payment/client.py`
- MNEE SDK: `../payment/mnee_sdk.py`
- Architecture: `../../FINAL_PROJECT_OVERVIEW.md`
