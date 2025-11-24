# Guardian Integration - Migration Guide

## Summary of Changes

This document explains the refactoring from direct private key usage to Guardian Service architecture.

## What Changed?

### 1. New Component: Guardian Service

**Location:** `backend/guardian/service.py`

**Purpose:** Isolated key management service that is the **sole holder** of `TREASURY_PRIVATE_KEY`.

**Endpoints:**
- `POST /guardian/quote` - Pre-check payment feasibility
- `POST /guardian/pay` - Execute on-chain payment
- `GET /guardian/balance` - Query treasury balance

### 2. Refactored: Payment Client

**Location:** `backend/payment/client.py`

**Changes:**

#### Before (Insecure):
```python
class PaymentClient:
    def __init__(self, policy_engine=None):
        self.mnee = Mnee(...)
        self.treasury_key = os.getenv("TREASURY_PRIVATE_KEY")  # BAD: Direct key access

    def pay_for_service(...):
        response = self.mnee.pay_for_service(
            ...,
            private_key=self.treasury_key  # BAD: Direct signing
        )
```

#### After (Secure):
```python
class PaymentClient:
    def __init__(self, policy_engine=None):
        # No private key stored
        # Connects to Guardian Service via HTTP

    def pay_for_service(...):
        # Step 1: Policy check (unchanged)
        decision = self.policy_engine.evaluate(...)

        # Step 2: Guardian quote
        quote_response = httpx.post(f"{GUARDIAN_URL}/guardian/quote", ...)

        # Step 3: Guardian pay
        pay_response = httpx.post(f"{GUARDIAN_URL}/guardian/pay", ...)
```

### 3. Updated: Configuration

**File:** `backend/.env.example`

**Added:**
```bash
# Guardian Service Configuration
GUARDIAN_URL=http://localhost:8100
GUARDIAN_PORT=8100
MNEE_ENV=local
```

**Note:** `TREASURY_PRIVATE_KEY` still in `.env` but **only Guardian uses it**.

### 4. Updated: Startup Script

**File:** `start_all.sh`

**Added:**
- `start_guardian()` function
- `stop_guardian()` function
- Guardian starts between providers and backend
- Guardian port 8100 in service list

## Migration Steps

### For Existing Deployments

If you have an existing Omni-Agent deployment:

#### Step 1: Pull Latest Code
```bash
git pull origin main
```

#### Step 2: Update Environment
```bash
cd backend
cp .env .env.backup

# Add Guardian config to .env
echo "" >> .env
echo "# Guardian Service Configuration" >> .env
echo "GUARDIAN_URL=http://localhost:8100" >> .env
echo "GUARDIAN_PORT=8100" >> .env
echo "MNEE_ENV=local" >> .env
```

#### Step 3: Stop Existing Services
```bash
./start_all.sh stop
```

#### Step 4: Restart with Guardian
```bash
./start_all.sh
```

Verify Guardian is running:
```bash
curl http://localhost:8100/
```

Expected response:
```json
{
  "service": "MNEE Guardian",
  "status": "operational",
  "has_private_key": true,
  "environment": "local"
}
```

### For New Deployments

Follow standard setup in `README.md` - Guardian is now part of default startup.

## Verification

### 1. Check All Services Running

```bash
./start_all.sh status
```

Should show:
```
Hardhat Node:          RUNNING
Guardian Service:      RUNNING (PID: xxx)
Backend API:           RUNNING (PID: xxx)
...
```

### 2. Test Payment Flow

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"agent_id":"user-agent","message":"Generate a test image"}'
```

Check logs:
```bash
# Guardian logs
tail -f logs/guardian.log

# Should see:
# [GUARDIAN] Quote request: user-agent -> IMAGE_GEN_PREMIUM x1
# [GUARDIAN] Quote result: can_pay=true
# [GUARDIAN] Payment request:
# [GUARDIAN] Payment successful!
```

### 3. Verify Payment Client Not Using Keys

```bash
# This should NOT exist in Payment Client code
grep -n "self.treasury_key" backend/payment/client.py

# Should return nothing (or only in comments)
```

## Benefits

### Security

- **Isolated Keys**: Private key only in Guardian process
- **Minimal Surface**: Guardian has simple, auditable API
- **TEE-Ready**: Can migrate Guardian to SGX without changing app

### Compliance

- **MNEE Requirements**: Meets all official requirements
  - Real MNEE transfers
  - Self-transfers allowed
  - Intermediate contracts OK
  - Infrastructure agents acceptable

### Operational

- **Separate Logs**: All signing operations in `logs/guardian.log`
- **Easy Monitoring**: Single endpoint to check key operations
- **Graceful Degradation**: Backend can detect Guardian unavailability

## Rollback

If you need to rollback to old architecture:

```bash
# Restore old Payment Client
cd backend/payment
cp client_old_backup.py client.py

# Remove Guardian from .env
sed -i '/Guardian Service/d' .env
sed -i '/GUARDIAN_URL/d' .env
sed -i '/GUARDIAN_PORT/d' .env

# Restart without Guardian
./start_all.sh stop
./start_all.sh
```

**Note:** Old architecture is **not recommended** for production.

## Common Issues

### Issue 1: Guardian Won't Start

**Symptom:**
```
RuntimeError: TREASURY_PRIVATE_KEY must be set for Guardian Service
```

**Fix:**
```bash
cd backend
grep TREASURY_PRIVATE_KEY .env

# If missing, add it
echo "TREASURY_PRIVATE_KEY=0x..." >> .env
```

### Issue 2: Payment Client Can't Reach Guardian

**Symptom:**
```
[PAYMENT_CLIENT] Failed to connect to Guardian: Connection refused
```

**Fix:**
```bash
# Check Guardian is running
curl http://localhost:8100/
# If not, check logs
tail -f logs/guardian.log
```

### Issue 3: Payments Failing After Migration

**Symptom:**
```
Guardian rejected: Insufficient treasury balance
```

**Fix:**
```bash
# Check balance
curl http://localhost:8100/guardian/balance

# If low, fund treasury (on Hardhat fork)
npx hardhat console --network localhost
> await mnee.transfer(treasuryAddress, ethers.parseEther("1000"))
```

## Performance Impact

Guardian adds minimal latency:
- Quote endpoint: ~10-50ms (no blockchain call)
- Pay endpoint: ~500-2000ms (blockchain transaction)
- Balance endpoint: ~100-300ms (blockchain read)

This is **acceptable** for the security benefit.

## Next Steps

After migration is complete:

1. **Test Full Flow**: Run e2e tests (see `TEST_PLAN.md`)
2. **Monitor Logs**: Watch `logs/guardian.log` for anomalies
3. **Update Docs**: Update any custom documentation
4. **Consider TEE**: Plan TEE migration for production

## Questions?

- **Architecture**: See `FINAL_PROJECT_OVERVIEW.md`
- **Guardian Details**: See `backend/guardian/README.md`
- **MNEE Requirements**: See `MNEE_SDK.md`
