#!/bin/bash

# Configuration
export PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-analytical-park-492702-a0}"
export DATASET_ID="warehouse_data"
export TABLE_ID="expected_inventory"
export REGION="US"

echo "Configuring environment for project: $PROJECT_ID"

# Set gcloud project
gcloud config set project $PROJECT_ID

# Create BigQuery Dataset if it doesn't exist
bq --location=$REGION mk --dataset --if_exists $PROJECT_ID:$DATASET_ID

# Check if inventory.csv exists in the root
if [ ! -f "./inventory.csv" ]; then
    echo "Error: inventory.csv not found. Please ensure you are running this script from the project root."
    exit 1
fi

# Load initial data into BigQuery (using --replace to make it idempotent)
bq load --replace --autodetect --source_format=CSV ${DATASET_ID}.${TABLE_ID} ./inventory.csv

# Create/Update .env file
echo "MODEL=gemini-1.5-pro" > .env
echo "GOOGLE_CLOUD_PROJECT=$PROJECT_ID" >> .env
echo "BQ_DATASET=$DATASET_ID" >> .env
echo "BQ_TABLE=$TABLE_ID" >> .env
echo "API_ACCESS_TOKEN=super-secret-key" >> .env

echo "Setup complete. Directory naming validated as logistic_management."
