from fastapi import FastAPI
import uvicorn
import random
from pydantic import BaseModel
import uuid

app = FastAPI(title="ImageGen Provider", version="1.0.0")

IMAGES = [
    "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?q=80&w=2564&auto=format&fit=crop",
    "https://images.unsplash.com/photo-1534528741775-53994a69daeb?q=80&w=2864&auto=format&fit=crop",
    "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?q=80&w=2787&auto=format&fit=crop"
]

class ImageRequest(BaseModel):
    prompt: str
    taskId: str = None
    serviceCallHash: str = None

@app.get("/")
def root():
    return {"service": "IMAGE_GEN_PREMIUM", "status": "running", "version": "1.0.0"}

@app.post("/image/generate")
def generate_image(request: ImageRequest):
    """
    Generate an image based on a prompt.
    Spec: POST /image/generate with {prompt, taskId, serviceCallHash}
    Returns: {imageUrl, taskId, serviceCallHash}
    
    The serviceCallHash binds this service invocation to the on-chain payment.
    """
    task_id = request.taskId or str(uuid.uuid4())
    service_call_hash = request.serviceCallHash
    
    # In production, provider should verify:
    # 1. PaymentExecuted event exists on-chain with matching serviceCallHash
    # 2. Payment amount matches service cost
    # For MVP, we trust the backend
    
    # Mock image generation - in production would call Stable Diffusion/DALL-E
    image_url = random.choice(IMAGES)
    
    result = {
        "imageUrl": image_url,
        "taskId": task_id,
        "prompt": request.prompt,
        "status": "completed"
    }
    
    # Echo back serviceCallHash for verification
    if service_call_hash:
        result["serviceCallHash"] = service_call_hash
    
    return result

@app.get("/health")
def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
