from fastapi import FastAPI
import uvicorn
import random

app = FastAPI()

@app.get("/price/{symbol}")
def get_price(symbol: str):
    # Mock prices
    base_price = 3000.0 if symbol.upper() == "ETH" else 1.0
    volatility = random.uniform(-0.05, 0.05)
    current_price = base_price * (1 + volatility)
    
    return {
        "symbol": symbol.upper(),
        "price": round(current_price, 2),
        "currency": "USD"
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
