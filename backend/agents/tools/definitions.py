import requests
from langchain.tools import tool

# We assume providers are running on localhost ports
IMAGE_GEN_URL = "http://localhost:8001/generate"
PRICE_ORACLE_URL = "http://localhost:8002/price"
BATCH_COMPUTE_URL = "http://localhost:8003/submit"
LOG_ARCHIVE_URL = "http://localhost:8004/archive"

def generate_image_tool(prompt: str):
    """Generates an image based on a prompt."""
    try:
        resp = requests.post(IMAGE_GEN_URL, params={"prompt": prompt})
        return resp.json()
    except Exception as e:
        return {"error": str(e)}

def get_price_tool(symbol: str):
    """Gets the current price of a crypto asset."""
    try:
        resp = requests.get(f"{PRICE_ORACLE_URL}/{symbol}")
        return resp.json()
    except Exception as e:
        return {"error": str(e)}

def submit_batch_job_tool(payload: str):
    """Submits a heavy batch compute job."""
    try:
        resp = requests.post(BATCH_COMPUTE_URL, json={"data": payload})
        return resp.json()
    except Exception as e:
        return {"error": str(e)}

def archive_log_tool(content: str, agent_id: str):
    """Archives a log entry."""
    try:
        resp = requests.post(LOG_ARCHIVE_URL, json={"content": content, "agent_id": agent_id})
        return resp.json()
    except Exception as e:
        return {"error": str(e)}
