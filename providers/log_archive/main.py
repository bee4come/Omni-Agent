from fastapi import FastAPI
import uvicorn
from pydantic import BaseModel

app = FastAPI()

class LogEntry(BaseModel):
    agent_id: str
    content: str
    level: str = "INFO"

LOGS = []

@app.post("/archive")
def archive_log(entry: LogEntry):
    LOGS.append(entry)
    return {"status": "archived", "total_logs": len(LOGS)}

@app.get("/stats")
def get_stats():
    return {"total_logs": len(LOGS)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8004)
