import os
import logging
import random
from google.cloud import bigquery
from google.api_core.exceptions import NotFound
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

def ingest_inventory_csv(tool_context: ToolContext, csv_path: str = "/home/piyush_knt/logistic_management/inventory.csv") -> dict[str, str]:
    """Initializes BigQuery by loading the local inventory CSV data."""
    try:
        cfg = get_bq_config()
        client = bigquery.Client(project=cfg["PROJECT_ID"])
        
        # Ensure the dataset exists before attempting to load data
        dataset_ref = client.dataset(cfg["DATASET_ID"])
        try:
            client.get_dataset(dataset_ref)
        except NotFound:
            logger.info(f"Dataset {cfg['DATASET_ID']} not found. Creating it...")
            client.create_dataset(bigquery.Dataset(dataset_ref))

        table_ref = f"{cfg['PROJECT_ID']}.{cfg['DATASET_ID']}.{cfg['TABLE_ID']}"

        job_config = bigquery.LoadJobConfig(
            source_format=bigquery.SourceFormat.CSV,
            skip_leading_rows=1,
            autodetect=True,
            write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        )

        if not os.path.exists(csv_path):
            return {"status": "error", "message": f"CSV file not found at {csv_path}"}

        with open(csv_path, "rb") as source_file:
            load_job = client.load_table_from_file(source_file, table_ref, job_config=job_config)
            load_job.result()  # Wait for completion

        table = client.get_table(table_ref)
        return {
            "status": "success",
            "message": f"Initialized {table_ref} with {table.num_rows} records from CSV."
        }
    except Exception as e:
        logger.error(f"Ingestion error: {e}")
        return {"status": "error", "message": str(e)}

def update_inventory_data(tool_context: ToolContext, items: list[dict]) -> dict[str, str]:
    """Streams new inventory records into BigQuery for scaling everyday inputs."""
    try:
        cfg = get_bq_config()
        client = bigquery.Client(project=cfg["PROJECT_ID"])
        table_id = f"{cfg['PROJECT_ID']}.{cfg['DATASET_ID']}.{cfg['TABLE_ID']}"

        errors = client.insert_rows_json(table_id, items)
        if not errors:
            return {"status": "success", "message": f"Ingested {len(items)} new records."}
        return {"status": "error", "message": f"Encountered errors: {errors}"}
    except Exception as e:
        logger.error(f"Update error: {e}")
        return {"status": "error", "message": str(e)}

def analyze_drone_media(tool_context: ToolContext, media_uri: str) -> dict[str, str]:
    """
    Analyzes drone media (images/videos) stored in GCS using multimodal AI.
    Returns a description of detected items and their estimated counts.
    """
    # In production, this would call vertexai.generative_models.GenerativeModel
    # to process the image/video Part.
    logger.info(f"Analyzing multimodal data from: {media_uri}")
    
    # Simulated AI response extracting data from a video/image
    return {
        "status": "success",
        "analysis": "Visual scan identifies SKU-001. Estimated count: 142 units. Condition: Normal.",
        "detected_sku": "SKU-001"
    }

def audit_drone_data(tool_context: ToolContext, query_location: str, visual_observation: str = None) -> dict[str, str]:
    """Compares drone observations (visual or metadata) against the expected database records."""
    try:
        cfg = get_bq_config()
        client = bigquery.Client(project=cfg["PROJECT_ID"])
        query = f"""
            SELECT expected_count, description, sku
            FROM `{cfg['PROJECT_ID']}.{cfg['DATASET_ID']}.{cfg['TABLE_ID']}`
            WHERE location_tag = @location
        """
        job_config = bigquery.QueryJobConfig(
            query_parameters=[bigquery.ScalarQueryParameter("location", "STRING", query_location)]
        )
        query_job = client.query(query, job_config=job_config)
        results = list(query_job.result())

        if results:
            expected_count, description, sku = results[0]
            # If visual_observation is provided by analyze_drone_media, the agent can use it to compare.
            info_source = visual_observation if visual_observation else "simulated sensor data"
            
            return {
                "status": "success",
                "data": f"Audit for {query_location}: '{description}' ({sku}). Expected: {expected_count}. Drone observation: {info_source}."
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
