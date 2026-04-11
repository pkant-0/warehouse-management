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
-   BigQuery API enabled in project `analytical-park-492702-a0`.

### Installation

1.  Clone the repository:
    ```bash
    git clone https://github.com/pkant-0/warehouse-management.git
    cd warehouse-management
    ```

2.  Install dependencies:
    ```bash
    pip install fastapi uvicorn google-adk python-dotenv google-cloud-logging google-cloud-bigquery
    ```

3.  **Run Setup Script**:
    ```bash
    chmod +x setup/setup_env.sh
    ./setup/setup_env.sh
    ```

## Usage

1.  **Run the API server**:
    ```bash
    uvicorn api:app --reload
    ```

2.  **Using Docker**:
    ```bash
    docker build -t warehouse-agent .
    docker run -p 8000:8000 --env-file .env warehouse-agent
    ```
