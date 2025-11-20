from fastapi import FastAPI, BackgroundTasks
import uvicorn
import time
import uuid
from pydantic import BaseModel

app = FastAPI(title="BatchCompute Provider", version="1.0.0")

JOBS = {}

class BatchJobRequest(BaseModel):
    data: str
    taskId: str = None
    serviceCallHash: str = None

def process_job(job_id: str):
    """Simulate heavy batch processing"""
    time.sleep(5)  # Simulate work
    JOBS[job_id]['status'] = 'finished'
    JOBS[job_id]['result'] = f'Analysis complete: Processed {len(JOBS[job_id]["payload"])} bytes. Found 42 anomalies.'

@app.get("/")
def root():
    return {"service": "BATCH_COMPUTE", "status": "running", "version": "1.0.0"}

@app.post("/batch/submit")
def submit_job(request: BatchJobRequest, background_tasks: BackgroundTasks):
    """
    Submit a batch compute job.
    Spec: POST /batch/submit with {data, taskId, serviceCallHash}
    Returns: {jobId, status, taskId, serviceCallHash}
    """
    job_id = str(uuid.uuid4())
    JOBS[job_id] = {
        'status': 'running',
        'payload': request.data,
        'result': None,
        'taskId': request.taskId,
        'serviceCallHash': request.serviceCallHash
    }
    
    background_tasks.add_task(process_job, job_id)
    
    result = {
        "jobId": job_id,
        "status": "running"
    }
    
    # Echo back anti-spoofing metadata
    if request.taskId:
        result["taskId"] = request.taskId
    if request.serviceCallHash:
        result["serviceCallHash"] = request.serviceCallHash
    
    return result

@app.get("/batch/status")
def get_status(jobId: str, taskId: str = None, serviceCallHash: str = None):
    """
    Get batch job status.
    Spec: GET /batch/status?jobId=xxx&taskId=...&serviceCallHash=...
    Returns: {status, result?, taskId?, serviceCallHash?}
    """
    job = JOBS.get(jobId)
    if not job:
        return {"status": "not_found"}
    
    response = {"status": job['status']}
    if job.get('result'):
        response['result'] = job['result']
    
    # Include anti-spoofing metadata
    if job.get('taskId'):
        response['taskId'] = job['taskId']
    if job.get('serviceCallHash'):
        response['serviceCallHash'] = job['serviceCallHash']
    
    return response

@app.get("/health")
def health():
    return {"status": "healthy", "active_jobs": len([j for j in JOBS.values() if j['status'] == 'running'])}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8003)
