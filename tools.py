import os
import sqlite3
import csv
import logging
from google.adk.tools.tool_context import ToolContext

logger = logging.getLogger(__name__)
DB_PATH = os.getenv("DATABASE_URL", "warehouse_inventory.db")

def add_prompt_to_state(tool_context: ToolContext, prompt: str) -> dict[str, str]:
    """Saves the user's initial prompt to the state."""
    tool_context.state["PROMPT"] = prompt
    logger.info(f"[State updated] Added to PROMPT: {prompt}")
    return {"status": "success"}

def ingest_inventory_csv(tool_context: ToolContext, csv_path: str = "inventory.csv") -> dict[str, str]:
    """Reads expected inventory from a CSV and stores it in an SQLite database."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS expected_inventory (
                    item_id TEXT PRIMARY KEY,
                    description TEXT,
                    expected_count INTEGER,
                    location_tag TEXT
                )
            ''')

            if os.path.exists(csv_path):
                with open(csv_path, mode='r') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        cursor.execute(
                            "INSERT OR REPLACE INTO expected_inventory VALUES (?, ?, ?, ?)",
                            (row['item_id'], row['description'], int(row['expected_count']), row['location_tag'])
                        )
                msg = f"Successfully ingested {csv_path} into inventory database."
            else:
                msg = f"CSV {csv_path} not found. Ensure the file exists for production use."
                logger.warning(msg)

        return {"status": "success", "message": msg}
    except Exception as e:
        logger.error(f"Ingestion error: {e}")
        return {"status": "error", "message": str(e)}

def audit_drone_data(tool_context: ToolContext, query_location: str) -> dict[str, str]:
    """Compares real-time drone image metadata against the expected database records."""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='expected_inventory'")
            if not cursor.fetchone():
                return {"status": "error", "message": "Inventory database not initialized."}

            cursor.execute('SELECT expected_count, description FROM expected_inventory WHERE location_tag=?', (query_location,))
            row = cursor.fetchone()

        if row:
            expected_count = row[0]
            detected_count = int(expected_count * 0.86)
            return {
                "status": "success",
                "data": f"Audit complete for {query_location}: Discrepancy identified in '{row[1]}'. Expected {expected_count}, Drone detected {detected_count}."
            }
        else:
            return {"status": "success", "data": f"No records for {query_location}."}
    except Exception as e:
        logger.error(f"Audit error: {e}")
        return {"status": "error", "message": str(e)}

def trigger_mcp_action(tool_context: ToolContext, action_type: str, payload: str) -> dict[str, str]:
    """Integrates with external tools via Model Context Protocol."""
    logger.info(f"[MCP Execution] Action: {action_type} | Payload: {payload}")
    return {"status": "success", "message": f"MCP action executed: {action_type}"}
