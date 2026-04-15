import os
import logging
import random
from google.cloud import bigquery
from google.adk.tools.tool_context import ToolContext

logger = logging.getLogger(__name__)

def get_bq_config():
    """Helper to get current BigQuery configuration from environment."""
    return {
        "PROJECT_ID": os.getenv("GOOGLE_CLOUD_PROJECT"),
        "DATASET_ID": os.getenv("BQ_DATASET"),
        "TABLE_ID": os.getenv("BQ_TABLE")
    }

def add_prompt_to_state(tool_context: ToolContext, prompt: str) -> dict[str, str]:
    """Saves the user's initial prompt to the state."""
    tool_context.state["PROMPT"] = prompt
    logger.info(f"[State updated] Added to PROMPT: {prompt}")
    return {"status": "success"}

def ingest_inventory_csv(tool_context: ToolContext, csv_path: str = "inventory.csv") -> dict[str, str]:
    """Verifies BigQuery connectivity and ensures the dataset is ready."""
    try:
        cfg = get_bq_config()
        client = bigquery.Client(project=cfg["PROJECT_ID"])
        table_ref = f"{cfg['PROJECT_ID']}.{cfg['DATASET_ID']}.{cfg['TABLE_ID']}"
        table = client.get_table(table_ref)

        # Log connectivity for debugging
        logger.info(f"Connected to BigQuery: {table_ref}")
        print(f"DEBUG: Connected to BigQuery: {table_ref}")

        if table.num_rows == 0:
            return {"status": "warning", "message": f"Table {table_ref} is empty. Ensure setup_env.sh was run correctly."}

        return {
            "status": "success",
            "message": f"Connected to BigQuery table {table_ref}. Ready for audit with {table.num_rows} records."
        }
    except Exception as e:
        logger.error(f"Ingestion error: {e}")
        return {"status": "error", "message": str(e)}

def audit_drone_data(tool_context: ToolContext, query_location: str) -> dict[str, str]:
    """Compares real-time drone image metadata against the expected database records."""
    try:
        cfg = get_bq_config()
        client = bigquery.Client(project=cfg["PROJECT_ID"])
        query = f"""
            SELECT expected_count, description
            FROM `{cfg['PROJECT_ID']}.{cfg['DATASET_ID']}.{cfg['TABLE_ID']}`
            WHERE location_tag = @location
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[bigquery.ScalarQueryParameter("location", "STRING", query_location)]
        )
        query_job = client.query(query, job_config=job_config)
        results = list(query_job.result())

        if results:
            expected_count, description = results[0]
            # Simulate realistic variance (85% to 100% detection)
            detected_count = int(expected_count * random.uniform(0.85, 1.0))
            return {
                "status": "success",
                "data": f"Audit complete for {query_location}: Discrepancy identified in '{description}'. Expected {expected_count}, Drone detected {detected_count}."
            }
        else:
            return {"status": "success", "data": f"No records for {query_location}."}
    except Exception as e:
        logger.error(f"Audit error: {e}")
        return {"status": "error", "message": str(e)}

def trigger_mcp_action(tool_context: ToolContext, action_type: str, payload: str) -> dict[str, str]:
    """
    Integrates with external tools via Model Context Protocol (MCP).
    Use this for scheduling, notifications, or task creation in external systems.
    """
    # In a real scenario, this would call an MCP server endpoint.
    # Here we simulate the successful scheduling of a logistics task.
    execution_details = {
        "action": action_type,
        "timestamp": "2023-10-27T10:00:00Z",
        "payload_received": payload
    }
    logger.info(f"[MCP Execution] {execution_details}")
    return {"status": "success", "message": f"Successfully triggered {action_type} via MCP."}
