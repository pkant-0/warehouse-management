from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel
import time
import logging

from agent import coordinator_agent

app = FastAPI(
    title="Logistic Warehouse Management API",
    version="1.0.0",
    description="Production-ready API for warehouse multi-agent workflows."
)

class AuditRequest(BaseModel):
    prompt: str
    location: str = "Zone-A"

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "healthy", "timestamp": time.time()}

@app.post("/api/v1/warehouse/audit")
async def run_warehouse_audit(request: AuditRequest):
    """
    Triggers the multi-agent warehouse auditing workflow.
    """
    try:
        agent_input = f"Audit inventory for {request.location}. {request.prompt}"
        result = coordinator_agent.run(agent_input)

        # Extract the text content from the agent response object
        output_text = getattr(result, 'text', str(result))

        return {
            "status": "completed",
            "output": output_text
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
