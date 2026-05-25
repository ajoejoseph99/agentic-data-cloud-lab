ADK Enterprise Data Lab

This repository demonstrates a production-grade Agentic Data Cloud application using the Google Agent Development Kit (ADK), the Model Context Protocol (MCP), and a Multi-Agent Mesh architecture.

Architecture

FastAPI Service (main.py): A secure REST API entry point for the agent mesh.

Multi-Agent Mesh (agents_mesh.py): Decouples logic into a Planner Agent (strategy formulation) and an Executor Agent (tool execution).

Enterprise Tooling (enterprise_agent/agent.py): Secures BigQuery access using ambient Google Cloud identities and an MCP tool abstraction layer, preventing hardcoded credentials or SQL injection vulnerabilities.

Quickstart

Environment Variables:
Ensure your Google Cloud Project is set:

export GOOGLE_CLOUD_PROJECT="your-project-id"



Install Dependencies:

Since pyproject.toml is a configuration file, install the project in editable mode:

pip install -e .



Seed the Database:
Inject the mock Q1 transaction logs into BigQuery:

python seed_mock_data.py



Run the API locally:
Start the FastAPI web server using Uvicorn:

uvicorn main:app --reload --host 0.0.0.0 --port 8080



Test the Agent Mesh:
Open a new terminal and send a POST request:

curl -X POST "http://localhost:8080/query" \
     -H "Content-Type: application/json" \
     -d '{"user_input": "What is the total revenue for transactions that were delayed in Q1?"}'



Cloud Run Deployment

To deploy this securely as an Agentic microservice:

gcloud run deploy enterprise-data-agent \
  --source . \
  --service-account="agentic-data-sa@$GOOGLE_CLOUD_PROJECT.iam.gserviceaccount.com" \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=$GOOGLE_CLOUD_PROJECT" \
  --region="us-central1" \
  --allow-unauthenticated 

