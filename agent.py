import os
import logging
from dotenv import load_dotenv

import google.cloud.logging
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

load_dotenv()
model_name = os.getenv("MODEL", "gemini-1.5-pro")

# --- Agent Configuration ---
inventory_auditor = Agent(
    name="inventory_auditor",
    model=model_name,
    description="Ingests CSV data and parses drone metadata to identify inventory discrepancies.",
    instruction="Use 'ingest_inventory_csv' to initialize the database from the expected inventory CSV. Use 'audit_drone_data' to cross-reference drone scans with expected records. Document all found discrepancies and output them clearly. PROMPT: { PROMPT }",
    tools=[ingest_inventory_csv, audit_drone_data],
    output_key="audit_findings"
)

forecasting_agent = Agent(
    name="forecasting_agent",
    model=model_name,
    description="Analyzes stock depletion and triggers proactive external actions.",
    instruction="Review the AUDIT_FINDINGS. If items are depleting faster than expected or running low, use 'trigger_mcp_action' to proactively alert suppliers via email or assign a restock task. AUDIT_FINDINGS: { audit_findings }",
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
    instruction="Acknowledge the user's request, save it using 'add_prompt_to_state', and then call the 'warehouse_workflow' tool to begin the audit process.",
    tools=[add_prompt_to_state, warehouse_workflow]
)
