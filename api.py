import os
from fastapi import FastAPI, HTTPException, Request, Depends, Security
from fastapi.security.api_key import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import time
import logging
from agent import coordinator_agent

app = FastAPI(
    title="Logistic Warehouse Management API",
    version="1.0.0",
    description="Production-ready API for warehouse multi-agent workflows."
)

# Enable CORS for external UIs
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_KEY = os.getenv("API_ACCESS_TOKEN")
if not API_KEY:
    logging.error("API_ACCESS_TOKEN environment variable not set.")

api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=False)

async def get_api_key(api_key_header: str = Security(api_key_header)):
    if API_KEY and api_key_header == API_KEY:
        return api_key_header
    raise HTTPException(status_code=403, detail="Could not validate credentials")

class InventoryItem(BaseModel):
    sku: str
    description: str
    location_tag: str
    expected_count: int

class AuditRequest(BaseModel):
    prompt: str
    location: str = "Zone-A"

class IngestRequest(BaseModel):
    items: list[InventoryItem]

class DroneMediaAuditRequest(BaseModel):
    media_uri: str  # GCS URI: gs://bucket/drone_scan.mp4
    location: str

@app.post("/api/v1/warehouse/ingest")
def ingest_inventory(request: IngestRequest, api_key: str = Depends(get_api_key)):
    """
    Endpoint for bulk everyday data inputs to scale the system.
    """
    try:
        # Convert Pydantic models to dicts for the agent tool
        items_data = [item.model_dump() for item in request.items]
        agent_input = f"I have new inventory data to add: {items_data}"
        result = coordinator_agent.run(agent_input)
        return {"status": "success", "agent_response": result.text if hasattr(result, 'text') else str(result)}
    except Exception as e:
        logging.error(f"Ingestion error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process new data inputs.")

@app.post("/api/v1/warehouse/media-audit")
def run_media_audit(request: DroneMediaAuditRequest, api_key: str = Depends(get_api_key)):
    """
    Triggers an audit using AI analysis of drone images or video.
    """
    try:
        agent_input = (
            f"Perform a visual audit at {request.location}. "
            f"The drone media is stored at {request.media_uri}. "
            "Compare the visual evidence with the inventory ledger."
        )
        result = coordinator_agent.run(agent_input)
        return {"status": "success", "audit_report": result.text if hasattr(result, 'text') else str(result)}
    except Exception as e:
        logging.error(f"Media audit error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to process media audit.")
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

@app.get("/")
async def root():
    """Root endpoint providing documentation link."""
    return {"message": "Warehouse Management API is running. Visit /docs for UI."}

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {"status": "healthy", "timestamp": time.time()}

@app.post("/api/v1/warehouse/audit")
@app.post("/chat")
def run_warehouse_audit(request: AuditRequest, api_key: str = Depends(get_api_key)):
    """
    Triggers the multi-agent warehouse auditing workflow.
    """
    try:
        agent_input = f"Audit inventory for {request.location}. {request.prompt}"
        result = coordinator_agent.run(agent_input)

        # Extract the text content from the agent response object
        output_text = result.text if hasattr(result, 'text') else str(result)

        return {
            "status": "completed",
            "output": output_text
        }

    except Exception as e:
        logging.error(f"Error during audit workflow: {str(e)}")
        raise HTTPException(status_code=500, detail="The multi-agent workflow encountered an unexpected issue.")
