from fastapi import FastAPI
import uvicorn
from pydantic import BaseModel
import uuid

app = FastAPI(title="LogArchive Provider", version="1.0.0")

class LogEntry(BaseModel):
    content: str
    agent_id: str
    level: str = "INFO"
    taskId: str = None
    serviceCallHash: str = None

LOGS = []

@app.get("/")
def root():
    return {"service": "LOG_ARCHIVE", "status": "running", "version": "1.0.0"}

@app.post("/logs/archive")
def archive_log(entry: LogEntry):
    """
    Archive a log entry.
    Spec: POST /logs/archive with {content, agent_id, taskId, serviceCallHash}
    Returns: {archived: true, storageId, taskId, serviceCallHash}
    """
    storage_id = f"storage-{uuid.uuid4().hex[:12]}"
    
    log_record = {
        "storageId": storage_id,
        "agentId": entry.agent_id,
        "content": entry.content,
        "level": entry.level,
        "taskId": entry.taskId,
        "serviceCallHash": entry.serviceCallHash
    }
    
    LOGS.append(log_record)
    
    result = {
        "archived": True,
        "storageId": storage_id,
        "totalLogs": len(LOGS)
    }
    
    # Echo back anti-spoofing metadata
    if entry.taskId:
        result["taskId"] = entry.taskId
    if entry.serviceCallHash:
        result["serviceCallHash"] = entry.serviceCallHash
    
    return result

@app.get("/logs/stats")
def get_stats():
    return {"total_logs": len(LOGS)}

@app.get("/health")
def health():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8004)
