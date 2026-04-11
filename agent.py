import os
import logging
import google.cloud.logging
from dotenv import load_dotenv

# Load environment variables before importing tools to ensure they use correct config
load_dotenv()

from google.adk import Agent
from google.adk.agents import SequentialAgent

# Import tools from the decoupled logic module
from tools import add_prompt_to_state, ingest_inventory_csv, audit_drone_data, trigger_mcp_action

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
    description="Ingests CSV data and parses drone metadata to identify inventory discrepancies.",
    instruction="1. Call 'ingest_inventory_csv' to ensure the database is ready. 2. Use 'audit_drone_data' to compare drone scan results against the records. 3. Identify any missing items or count mismatches. 4. Pass the summary of discrepancies to the next agent.",
    tools=[ingest_inventory_csv, audit_drone_data],
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

coordinator_agent = Agent(
    name="coordinator",
    model=model_name,
    description="Primary routing agent that manages warehouse operations.",
    instruction="Acknowledge the user's request, save it using 'add_prompt_to_state', and then call the 'warehouse_workflow' tool to begin the audit process. Once the workflow is complete, provide a detailed summary of the findings and any actions taken to the user. If any tool returns an error, explain it clearly.",
    tools=[add_prompt_to_state, warehouse_workflow]
)
