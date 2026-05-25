# ADK Enterprise Data Lab

This repository demonstrates a production-grade Agentic Data Cloud application using the Google Agent Development Kit (ADK), the Model Context Protocol (MCP), and a Multi-Agent Mesh architecture.

The mesh does not require or use hardcoded dataset names, table names, or schemas. Instead, it dynamically discovers database catalogs, tables, and schemas using standard MCP BigQuery tools.

## Architecture

- **FastAPI Service (`main.py`)**: A secure REST API entry point for the agent mesh.
- **Multi-Agent Mesh (`agents_mesh.py`)**: Decouples logic into a Planner Agent (formulates strategy plans for schema discovery and querying) and an Executor Agent (executes the plan step-by-step using MCP BigQuery tools).
- **Enterprise Tooling (`enterprise_agent/agent.py`)**: Secures BigQuery access using ambient Google Cloud identities and an MCP tool abstraction layer, preventing hardcoded credentials or SQL injection vulnerabilities.

---

## Quickstart Setup & Run

Copy and run the following commands in your bash terminal to set up the environment, install the workspace package, seed the sandbox database, run the FastAPI server, and test the dynamic discovery query:

```bash
# 1. Set Google Cloud Project ID
export GOOGLE_CLOUD_PROJECT="<<YOUR_PROJECT_ID>>"

# 2. Install current package in editable mode
pip install -e .

# 3. Seed the sandbox database in BigQuery
python seed_mock_data.py

# 4. Start the FastAPI API Server with Uvicorn
PYTHONUNBUFFERED=1 GOOGLE_CLOUD_PROJECT=<<YOUR_PROJECT_ID>> uvicorn main:app --reload --host 0.0.0.0 --port 8080
```

Open a new terminal to query the mesh and test dynamic schema discovery:

```bash
# 5. Query the endpoint to test dynamic discovery
curl -X POST "http://localhost:8080/query" \
     -H "Content-Type: application/json" \
     -d '{"user_input": "What is the total revenue for transactions that were delayed in Q1?"}'
```

---

## Cloud Run Deployment

To deploy this securely as an Agentic microservice:

```bash
gcloud run deploy enterprise-data-agent \
  --source . \
  --service-account="agentic-data-sa@$GOOGLE_CLOUD_PROJECT.iam.gserviceaccount.com" \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=$GOOGLE_CLOUD_PROJECT" \
  --region="us-central1" \
  --allow-unauthenticated
```

