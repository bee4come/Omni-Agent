from fastapi import FastAPI
import uvicorn
import random

app = FastAPI()

IMAGES = [
    "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?q=80&w=2564&auto=format&fit=crop",
    "https://images.unsplash.com/photo-1534528741775-53994a69daeb?q=80&w=2864&auto=format&fit=crop",
    "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?q=80&w=2787&auto=format&fit=crop"
]

@app.post("/generate")
def generate_image(prompt: str):
    # In a real app, we would check payment event here.
    # For demo, we just return a random image.
    return {
        "status": "success",
        "url": random.choice(IMAGES),
        "prompt": prompt
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
