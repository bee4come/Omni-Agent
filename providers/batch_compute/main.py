from fastapi import FastAPI, BackgroundTasks
import uvicorn
import time
import uuid

app = FastAPI()

JOBS = {}

def process_job(job_id: str):
    time.sleep(10) # Simulate work
    JOBS[job_id]['status'] = 'completed'
    JOBS[job_id]['result'] = 'Analysis complete: 42 anomalies found.'

@app.post("/submit")
def submit_job(background_tasks: BackgroundTasks, payload: dict):
    job_id = str(uuid.uuid4())
    JOBS[job_id] = {'status': 'processing', 'payload': payload}
    
    background_tasks.add_task(process_job, job_id)
    
    return {"job_id": job_id, "status": "queued"}

@app.get("/status/{job_id}")
def get_status(job_id: str):
    return JOBS.get(job_id, {"status": "not_found"})

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003)
