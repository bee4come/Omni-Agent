from fastapi import FastAPI
import uvicorn
import random

app = FastAPI(title="PriceOracle Provider", version="1.0.0")

# Mock price database
MOCK_PRICES = {
    "ETH": 3000.0,
    "BTC": 60000.0,
    "MNEE": 1.0,  # Stable coin pegged to USD
}

@app.get("/")
def root():
    return {"service": "PRICE_ORACLE", "status": "running", "version": "1.0.0"}

@app.get("/price")
def get_price(base: str = "ETH", quote: str = "MNEE", taskId: str = None, serviceCallHash: str = None):
    """
    Get crypto price conversion.
    Spec: GET /price?base=ETH&quote=MNEE&taskId=...&serviceCallHash=...
    Returns: {base, quote, price, taskId, serviceCallHash}
    
    The serviceCallHash binds this service invocation to the on-chain payment.
    """
    base_upper = base.upper()
    quote_upper = quote.upper()
    
    # Get base price in USD
    base_price = MOCK_PRICES.get(base_upper, 1.0)
    quote_price = MOCK_PRICES.get(quote_upper, 1.0)
    
    # Add some volatility
    volatility = random.uniform(-0.02, 0.02)
    base_price = base_price * (1 + volatility)
    
    # Calculate conversion rate
    conversion_rate = base_price / quote_price
    
    result = {
        "base": base_upper,
        "quote": quote_upper,
        "price": round(conversion_rate, 2)
    }
    
    # Include anti-spoofing metadata
    if taskId:
        result["taskId"] = taskId
    if serviceCallHash:
        result["serviceCallHash"] = serviceCallHash
    
    return result

@app.get("/health")
def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
