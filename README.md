# Logistic Warehouse Management System

This project implements an AI-powered multi-agent system for warehouse inventory management and auditing. It leverages the Google Agent Development Kit (ADK) and Gemini models to orchestrate workflows between specialized agents.

## Architecture

The system consists of three primary agents:

1.  **Coordinator Agent**: The entry point that acknowledges requests and delegates tasks to the warehouse workflow.
2.  **Inventory Auditor**: Responsible for ingesting inventory data (from CSV) and comparing it against simulated drone scan data to identify discrepancies.
3.  **Forecasting Agent**: Analyzes audit findings to predict stockouts and triggers external actions (via MCP) such as notifying suppliers.

## Features

-   **Multi-Agent Orchestration**: Uses `SequentialAgent` to pipeline tasks from auditing to forecasting.
-   **Database Integration**: Uses SQLite (expandable to AlloyDB) for persisting expected inventory levels.
-   **Automated Auditing**: Simulates real-time drone data comparison.
-   **Extensible Tooling**: Built-in support for the Model Context Protocol (MCP) to interact with external systems.
-   **FastAPI Interface**: Provides a clean REST API to trigger the auditing workflow.

## Setup

### Prerequisites

-   Python 3.10+
-   Google Cloud Project with Vertex AI API enabled.
-   BigQuery API enabled in your Google Cloud Project.

### Installation

1.  Clone the repository:
    ```bash
    git clone https://github.com/pkant-0/warehouse-management.git logistic_management
    cd logistic_management
    ```

2.  Install dependencies:
    ```bash
    pip install fastapi uvicorn "google-adk>=0.1.0" python-dotenv google-cloud-logging google-cloud-bigquery
    ```

3.  **Run Setup Script**:
    ```bash
    chmod +x setup_env.sh
    ./setup_env.sh
    ```

## Usage

1.  **Run the API server**:
    ```bash
    # Locally
    uvicorn api:app --reload --port 8000

    # In Cloud Shell (for Web Preview)
    uvicorn api:app --reload --port 8080
    ```

## Deployment to Google Cloud Run

1.  **Enable Services**:
    ```bash
    gcloud services enable artifactregistry.googleapis.com run.googleapis.com
    ```

2.  **Build and Deploy**:
    Replace `PROJECT_ID` with `analytical-park-492702-a0`.
    ```bash
    gcloud run deploy warehouse_management \
      --source . \
      --region us-central1 \
      --project analytical-park-492702-a0 \
      --set-env-vars="GOOGLE_CLOUD_PROJECT=analytical-park-492702-a0,BQ_DATASET=warehouse_data,BQ_TABLE=expected_inventory,API_ACCESS_TOKEN=super-secret-key" \
      --allow-unauthenticated
    ```
