import os
import logging
import google.cloud.logging
from dotenv import load_dotenv

# Load environment variables before importing tools to ensure they use correct config
load_dotenv()

from google.adk import Agent
from google.adk.agents import SequentialAgent
from google.adk.tools.tool_context import ToolContext

# Import tools from the decoupled logic module
from tools import add_prompt_to_state, ingest_inventory_csv, audit_drone_data, trigger_mcp_action, update_inventory_data, analyze_drone_media

# --- Setup Logging and Environment ---
try:
    cloud_logging_client = google.cloud.logging.Client()
    cloud_logging_client.setup_logging()
except Exception as e:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logging.warning(f"Google Cloud Logging setup failed, using standard logger: {e}")

model_name = os.getenv("MODEL", "gemini-1.5-pro")

# --- Agent Configuration ---
inventory_auditor = Agent(
    name="inventory_auditor",
    model=model_name,
    description="Analyzes drone media and database records to identify discrepancies.",
    instruction="""
    1. Call 'ingest_inventory_csv' to ensure the database is ready if needed.
    2. If a media URI is provided, use 'analyze_drone_media' to extract visual counts.
    3. Use 'audit_drone_data' to retrieve expected counts from the database for the given location.
    4. Compare the visual findings against the database records.
    5. Pass a summary of discrepancies (e.g., SKU, expected vs actual, visual condition) to the next agent.
    """,
    tools=[ingest_inventory_csv, audit_drone_data, analyze_drone_media],
    output_key="audit_findings"
)

forecasting_agent = Agent(
    name="forecasting_agent",
    model=model_name,
    description="Analyzes audit findings to perform scheduling and task management.",
    instruction="Review the data in {audit_findings}. If discrepancies exist, use 'trigger_mcp_action' to create a 'RESTOCK_TASK' or 'SUPPLIER_ALERT'. Detail exactly what needs attention in the payload.",
    tools=[trigger_mcp_action],
    output_key="forecast_actions"
)

warehouse_workflow = SequentialAgent(
    name="warehouse_workflow",
    description="Multi-agent pipeline for auditing stock and forecasting bottlenecks.",
    sub_agents=[inventory_auditor, forecasting_agent]
)

def run_warehouse_workflow(tool_context: ToolContext) -> str:
    """
    Executes the multi-agent warehouse workflow for auditing and forecasting.
    """
    prompt = tool_context.state.get("PROMPT", "Perform inventory audit")
    result = warehouse_workflow.run(prompt)
    return result.text if hasattr(result, 'text') else str(result)

coordinator_agent = Agent(
    name="warehouse_coordinator",
    model=model_name,
    description="Primary routing agent that manages warehouse operations.",
    instruction="Acknowledge the user's request. If the request is to update inventory data, use 'update_inventory_data'. If the request is to perform an audit, save it using 'add_prompt_to_state' and call 'run_warehouse_workflow'. Once complete, provide a summary of actions taken.",
    tools=[add_prompt_to_state, run_warehouse_workflow, update_inventory_data]
)
