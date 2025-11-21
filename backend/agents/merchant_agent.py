from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from typing import Optional, Dict
import time
import uuid

# --- Models ---

class QuoteRequest(BaseModel):
    type: str = "QUOTE_REQUEST"
    serviceId: str
    taskId: str
    payload: Dict

class QuoteResponse(BaseModel):
    type: str = "QUOTE_RESPONSE"
    serviceId: str
    taskId: str
    unitPriceMNEE: str
    quantity: int
    providerAddress: str
    quoteId: str
    expiresAt: int
    terms: Optional[str] = None

class PaymentNotice(BaseModel):
    type: str = "PAYMENT_NOTICE"
    serviceId: str
    taskId: str
    paymentId: str
    serviceCallHash: str
    txHash: str
    quoteId: str

class ServiceResult(BaseModel):
    type: str = "SERVICE_RESULT"
    taskId: str
    serviceId: str
    status: str # "DELIVERED", "PENDING", "FAILED"
    data: Dict
    serviceCallHash: str
    deliveredAt: int

# --- Merchant Logic ---

router = APIRouter(prefix="/merchant", tags=["merchant"])

# Mock Database / State
active_quotes = {} # quoteId -> QuoteResponse
fulfilled_orders = {} # paymentId -> ServiceResult

# Configuration (In a real app, this would be in a DB or config file)
MERCHANT_WALLET_ADDRESS = "0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266" # Default Hardhat Account 0 (Testing)
SERVICES = {
    "IMAGE_GEN_PREMIUM": {
        "unitPrice": "1.0", # 1 MNEE
        "description": "Premium Cyberpunk Image Generation"
    },
    "DATA_ANALYSIS_BASIC": {
        "unitPrice": "0.5", # 0.5 MNEE
        "description": "Basic Dataset Analysis"
    }
}

@router.post("/quote", response_model=QuoteResponse)
async def create_quote(request: QuoteRequest):
    """
    Merchant Agent receives a request and generates a binding quote.
    """
    if request.serviceId not in SERVICES:
        raise HTTPException(status_code=404, detail="Service not offered by this merchant")
    
    service_info = SERVICES[request.serviceId]
    
    # Logic: Calculate price (could be dynamic based on payload complexity)
    # For MVP, it's static.
    
    quote_id = f"quote-{uuid.uuid4().hex[:8]}"
    expires_at = int(time.time()) + 300 # 5 minutes expiry
    
    quote = QuoteResponse(
        serviceId=request.serviceId,
        taskId=request.taskId,
        unitPriceMNEE=service_info["unitPrice"],
        quantity=1, # Default to 1 unit for now
        providerAddress=MERCHANT_WALLET_ADDRESS,
        quoteId=quote_id,
        expiresAt=expires_at,
        terms=f"Valid for 5 minutes. {service_info['description']}"
    )
    
    active_quotes[quote_id] = quote
    print(f"[Merchant] Generated Quote: {quote_id} for {request.serviceId} @ {quote.unitPriceMNEE} MNEE")
    return quote

@router.post("/deliver", response_model=ServiceResult)
async def deliver_service(notice: PaymentNotice):
    """
    Merchant Agent receives payment notice, verifies it (trust-based for MVP), and delivers goods.
    """
    
    # 1. Verify Quote existence
    if notice.quoteId not in active_quotes:
        raise HTTPException(status_code=400, detail="Invalid or expired quote ID")
        
    quote = active_quotes[notice.quoteId]
    
    # 2. Verify Payment Details (MVP: Trust the Client. Real: Check Chain)
    # In a real scenario, we would query the blockchain using web3.py here:
    # event = contract.events.PaymentExecuted.get_logs(argument_filters={'paymentId': notice.paymentId})
    # if not event: raise Error...
    
    print(f"[Merchant] Verifying Payment: {notice.paymentId} for Quote {notice.quoteId}...")
    time.sleep(1) # Simulate verification delay
    
    # 3. Generate Service Result
    # This is where the "Work" happens (e.g., generating the image)
    
    result_data = {}
    if notice.serviceId == "IMAGE_GEN_PREMIUM":
        result_data = {
            "imageUrl": "https://ipfs.io/ipfs/QmXyZ...", 
            "prompt": "cyberpunk avatar", # potentially from original payload
            "resolution": "1024x1024"
        }
    elif notice.serviceId == "DATA_ANALYSIS_BASIC":
         result_data = {
             "summary": "Analysis complete. Mean: 42, Median: 40.",
             "reportUrl": "https://merchant.com/reports/123.pdf"
         }
    
    result = ServiceResult(
        taskId=notice.taskId,
        serviceId=notice.serviceId,
        status="DELIVERED",
        data=result_data,
        serviceCallHash=notice.serviceCallHash,
        deliveredAt=int(time.time())
    )
    
    fulfilled_orders[notice.paymentId] = result
    print(f"[Merchant] Service Delivered for Task {notice.taskId}")
    
    return result
