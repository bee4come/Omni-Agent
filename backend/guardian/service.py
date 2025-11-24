"""
Guardian Service - Isolated Key Management Layer

Responsibilities:
1. Sole holder of TREASURY_PRIVATE_KEY
2. Provides /guardian/quote endpoint (pre-check)
3. Provides /guardian/pay endpoint (actual signing and payment)
4. Future migration target to TEE environment

Security Boundary:
- Only accepts structured payment requests
- Performs final hard checks before signing
- Never exposes private key to other services
"""

import os
from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from payment.mnee_sdk import Mnee

load_dotenv()

app = FastAPI(
    title="MNEE Guardian Service",
    description="Secure key management and transaction signing service",
    version="1.0.0"
)

# Global configuration
TREASURY_PRIVATE_KEY = os.getenv("TREASURY_PRIVATE_KEY", "")
if not TREASURY_PRIVATE_KEY:
    raise RuntimeError("TREASURY_PRIVATE_KEY must be set for Guardian Service")

# Initialize MNEE SDK
mnee = Mnee({
    "environment": os.getenv("MNEE_ENV", "local")
})

# Request/Response Models

class QuoteRequest(BaseModel):
    """Quote request - check if payment is possible"""
    agent_id: str
    service_id: str
    quantity: int
    estimated_unit_price: Optional[float] = None

class QuoteResponse(BaseModel):
    """Quote response"""
    can_pay: bool
    max_quantity: int
    reason: str
    treasury_balance: Optional[float] = None

class PayRequest(BaseModel):
    """Payment request - execute actual payment"""
    agent_id: str
    service_id: str
    task_id: str
    quantity: int
    service_call_hash: str

class PayResponse(BaseModel):
    """Payment response"""
    success: bool
    payment_id: Optional[str] = None
    tx_hash: Optional[str] = None
    reason: Optional[str] = None

# Guardian Logic - Final Hard Checks

def evaluate_payment_request(req: QuoteRequest) -> QuoteResponse:
    """
    Guardian-level hard checks (last line of defense)

    Only performs basic validation:
    1. quantity must be > 0
    2. Treasury balance sufficient (optional)
    3. Simple rate limiting (optional)

    Complex policy logic should be handled by upper-layer PolicyEngine
    """

    # Check 1: Basic parameter validation
    if req.quantity <= 0:
        return QuoteResponse(
            can_pay=False,
            max_quantity=0,
            reason="Invalid quantity: must be > 0"
        )

    # Check 2: Treasury balance (optional, may be slow)
    try:
        from eth_account import Account
        treasury_address = Account.from_key(TREASURY_PRIVATE_KEY).address
        balance_info = mnee.balance(treasury_address)
        treasury_balance = balance_info.get('decimalAmount', 0.0)

        if treasury_balance <= 0:
            return QuoteResponse(
                can_pay=False,
                max_quantity=0,
                reason="Insufficient treasury balance",
                treasury_balance=treasury_balance
            )
    except Exception as e:
        print(f"[GUARDIAN] Warning: Failed to check balance: {e}")

    # Check 3: Simple quantity limit (hardcoded, can be configurable later)
    MAX_QUANTITY_PER_CALL = 1000
    if req.quantity > MAX_QUANTITY_PER_CALL:
        return QuoteResponse(
            can_pay=True,
            max_quantity=MAX_QUANTITY_PER_CALL,
            reason=f"Quantity clamped to maximum {MAX_QUANTITY_PER_CALL}"
        )

    # All checks passed
    return QuoteResponse(
        can_pay=True,
        max_quantity=req.quantity,
        reason="Guardian checks passed"
    )

# API Endpoints

@app.get("/")
def health_check():
    """Health check endpoint"""
    return {
        "service": "MNEE Guardian",
        "status": "operational",
        "has_private_key": bool(TREASURY_PRIVATE_KEY),
        "environment": os.getenv("MNEE_ENV", "local")
    }

@app.post("/guardian/quote", response_model=QuoteResponse)
def guardian_quote(req: QuoteRequest):
    """
    Quote endpoint - pre-check if payment can proceed

    Fast check without executing actual payment
    Allows caller to know in advance if payment will succeed
    """
    try:
        print(f"[GUARDIAN] Quote request: {req.agent_id} -> {req.service_id} x{req.quantity}")
        response = evaluate_payment_request(req)
        print(f"[GUARDIAN] Quote result: can_pay={response.can_pay}, reason={response.reason}")
        return response
    except Exception as e:
        print(f"[GUARDIAN] Quote failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/guardian/pay", response_model=PayResponse)
def guardian_pay(req: PayRequest):
    """
    Payment endpoint - sign and execute on-chain payment

    This is the ONLY place where TREASURY_PRIVATE_KEY is used
    Caller must provide complete payment parameters and service_call_hash
    """
    try:
        print(f"[GUARDIAN] Payment request:")
        print(f"  Agent: {req.agent_id}")
        print(f"  Service: {req.service_id}")
        print(f"  Task: {req.task_id}")
        print(f"  Quantity: {req.quantity}")
        print(f"  ServiceCallHash: {req.service_call_hash}")

        # Final check
        if req.quantity <= 0:
            return PayResponse(
                success=False,
                payment_id=None,
                tx_hash=None,
                reason="Invalid quantity"
            )

        # Ensure approval (idempotent operation)
        print(f"[GUARDIAN] Ensuring approval...")
        mnee.ensure_approval(TREASURY_PRIVATE_KEY)

        # Execute payment via MNEE SDK
        print(f"[GUARDIAN] Executing payment via MNEE SDK...")
        response = mnee.pay_for_service(
            service_id=req.service_id,
            agent_id=req.agent_id,
            task_id=req.task_id,
            quantity=req.quantity,
            service_call_hash=req.service_call_hash,
            private_key=TREASURY_PRIVATE_KEY
        )

        ticket_id = response.ticketId
        tx_hash = response.rawtx

        print(f"[GUARDIAN] Payment successful!")
        print(f"  PaymentID: {ticket_id}")
        print(f"  TxHash: {tx_hash}")

        return PayResponse(
            success=True,
            payment_id=ticket_id,
            tx_hash=tx_hash,
            reason=None
        )

    except Exception as e:
        print(f"[GUARDIAN] Payment failed: {e}")
        return PayResponse(
            success=False,
            payment_id=None,
            tx_hash=None,
            reason=str(e)
        )

@app.get("/guardian/balance")
def get_treasury_balance():
    """
    Query Treasury balance

    Used for monitoring and auditing
    """
    try:
        from eth_account import Account
        treasury_address = Account.from_key(TREASURY_PRIVATE_KEY).address
        balance_info = mnee.balance(treasury_address)

        return {
            "success": True,
            "address": treasury_address,
            "balance_mnee": balance_info.get('decimalAmount', 0.0),
            "balance_wei": balance_info.get('rawAmount', '0')
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Main

if __name__ == "__main__":
    import uvicorn

    print("=" * 70)
    print("MNEE Guardian Service Starting...")
    print("=" * 70)
    print(f"Environment: {os.getenv('MNEE_ENV', 'local')}")
    print(f"Has Private Key: {bool(TREASURY_PRIVATE_KEY)}")
    print("=" * 70)

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv("GUARDIAN_PORT", "8100")),
        log_level="info"
    )
