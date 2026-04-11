from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import logging

from agent import coordinator_agent

app = FastAPI(
    title="Logistic Warehouse Management API",
    description="API to manage logistics and warehouse workflows via an LLM multi-agent system."
)

class AuditRequest(BaseModel):
    prompt: str
    location: str = "Zone-A"

@app.post("/api/v1/warehouse/audit")
async def run_warehouse_audit(request: AuditRequest):
    """
    Triggers the multi-agent warehouse auditing workflow.
    """
    try:
        # Build the initial request parameters for the coordinator agent
        agent_input = f"Audit inventory for {request.location}. {request.prompt}"
        # Agent.run returns an AgentRunResponse object; extract the final output string
        response = coordinator_agent.run(agent_input)
        return {"status": "success", "agent_response": response.text}
    except Exception as e:
        logging.error(f"Error running warehouse workflow: {e}")
        raise HTTPException(status_code=500, detail=str(e))
