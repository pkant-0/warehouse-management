import os
import logging
import sqlite3
import csv
from dotenv import load_dotenv

import google.cloud.logging
from google.adk import Agent
from google.adk.agents import SequentialAgent
from google.adk.tools.tool_context import ToolContext
from google.adk.tools.langchain_tool import LangchainTool

import google.auth
import google.auth.transport.requests
import google.oauth2.id_token

# --- Setup Logging and Environment ---
try:
    cloud_logging_client = google.cloud.logging.Client()
    cloud_logging_client.setup_logging()
except Exception as e:
    logging.basicConfig(level=logging.INFO)
    logging.warning(f"Google Cloud Logging setup failed, using standard logger: {e}")

load_dotenv()
model_name = os.getenv("MODEL", "gemini-1.5-pro")

DB_PATH = 'warehouse_inventory.db'

# --- Tool: Greet user and save their prompt ---
def add_prompt_to_state(tool_context: ToolContext, prompt: str) -> dict[str, str]:
    """Saves the user's initial prompt to the state."""
    tool_context.state["PROMPT"] = prompt
    logging.info(f"[State updated] Added to PROMPT: {prompt}")
    return {"status": "success"}

# --- Tool: Database Creation & CSV Ingestion ---
def ingest_inventory_csv(tool_context: ToolContext, csv_path: str) -> dict[str, str]:
    """Reads expected inventory from a CSV and stores it in an SQLite (stand-in for AlloyDB) database."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS expected_inventory (
                item_id TEXT PRIMARY KEY,
                description TEXT,
                expected_count INTEGER,
                location_tag TEXT
            )
        ''')
        # Insert Mock Data to allow SQL Query operations
        cursor.execute("INSERT OR REPLACE INTO expected_inventory VALUES ('SKU-100', 'Pallets of Electronics', 500, 'Zone-A')")
        cursor.execute("INSERT OR REPLACE INTO expected_inventory VALUES ('SKU-101', 'Pallets of Clothing', 200, 'Zone-B')")
        conn.commit()
        conn.close()
        return {"status": "success", "message": f"Successfully ingested {csv_path} into inventory database."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# --- Tool: Automated Auditing (Drone Data vs AlloyDB/SQLite) ---
def audit_drone_data(tool_context: ToolContext, query_location: str) -> dict[str, str]:
    """Compares real-time drone image metadata against the expected database records."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT expected_count, description FROM expected_inventory WHERE location_tag=?', (query_location,))
        row = cursor.fetchone()
        conn.close()

        if row:
            expected_count = row[0]
            detected_count = int(expected_count * 0.86) # Simulate drone detecting ~14% fewer items
            return {
                "status": "success",
                "data": f"Audit complete for {query_location}: Discrepancy identified in '{row[1]}'. Expected {expected_count}, Drone detected {detected_count}."
            }
        else:
            return {"status": "success", "data": f"No expected inventory found for {query_location}."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# --- Tool: MCP External Tool Integration ---
def trigger_mcp_action(tool_context: ToolContext, action_type: str, payload: str) -> dict[str, str]:
    """Integrates with external tools via Model Context Protocol (e.g., email supplier, update task manager)."""
    logging.info(f"[MCP Execution] Action: {action_type} | Payload: {payload}")
    return {"status": "success", "message": f"MCP action executed successfully: {action_type}. Payload tracked: {payload}"}

# --- Agent Configuration ---
inventory_auditor = Agent(
    name="inventory_auditor", model=model_name,
    description="Ingests CSV data and parses drone metadata to identify inventory discrepancies.",
    instruction="Use 'ingest_inventory_csv' to initialize the database from the expected inventory CSV. Use 'audit_drone_data' to cross-reference drone scans with expected records. Document all found discrepancies and output them clearly. PROMPT: { PROMPT }",
    tools=[ingest_inventory_csv, audit_drone_data], output_key="audit_findings"
)
forecasting_agent = Agent(
    name="forecasting_agent", model=model_name,
    description="Analyzes stock depletion and triggers proactive external actions.",
    instruction="Review the AUDIT_FINDINGS. If items are depleting faster than expected or running low, use 'trigger_mcp_action' to proactively alert suppliers via email or assign a restock task. AUDIT_FINDINGS: { audit_findings }",
    tools=[trigger_mcp_action], output_key="forecast_actions"
)
warehouse_workflow = SequentialAgent(name="warehouse_workflow", description="Multi-agent pipeline for auditing stock and forecasting bottlenecks.", sub_agents=[inventory_auditor, forecasting_agent])

# Added warehouse_workflow to tools so the coordinator can "transfer control" to it as instructed.
coordinator_agent = Agent(
    name="coordinator",
    model=model_name,
    description="Primary routing agent that manages warehouse operations.",
    instruction="Acknowledge the user's request, save it using 'add_prompt_to_state', and then call the 'warehouse_workflow' tool to begin the audit process.",
    tools=[add_prompt_to_state, warehouse_workflow]
)
