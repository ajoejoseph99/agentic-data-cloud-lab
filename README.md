# ADK Enterprise Data Lab

This repository demonstrates a production-grade Agentic Data Cloud application using the Google Agent Development Kit (ADK), the Model Context Protocol (MCP), and a Multi-Agent Mesh architecture.

The mesh does not require or use hardcoded dataset names, table names, or schemas. Instead, it dynamically discovers database catalogs, tables, and schemas using standard MCP BigQuery tools.

## Architecture

- **FastAPI Service (`main.py`)**: A secure REST API entry point for the agent mesh.
- **Multi-Agent Mesh (`agents_mesh.py`)**: Decouples logic into a Planner Agent (formulates strategy plans for schema discovery and querying) and an Executor Agent (executes the plan step-by-step using MCP BigQuery tools).
- **Enterprise Tooling (`enterprise_agent/agent.py`)**: Secures BigQuery access using ambient Google Cloud identities and an MCP tool abstraction layer, preventing hardcoded credentials or SQL injection vulnerabilities.

---

## GCP Prerequisites & Setup

Before running the quickstart, you must set up your Google Cloud project environment. Run the following commands to enable the required APIs, configure your local ADC credentials, and set up your billing project:

```bash
# 1. Authenticate with Google Cloud CLI
gcloud auth login
gcloud auth application-default login

# 2. Configure target GCP project
export GOOGLE_CLOUD_PROJECT="<<YOUR_PROJECT_ID>>"
gcloud config set project $GOOGLE_CLOUD_PROJECT

# 3. Enable BigQuery and Vertex AI APIs
gcloud services enable \
  bigquery.googleapis.com \
  aiplatform.googleapis.com
```

### Required IAM Permissions

Run the following script to grant the required IAM permissions to your logged-in Google Cloud account:

```bash
# Get the active account email automatically from gcloud config
USER_EMAIL=$(gcloud config get-value account)

# Grant Vertex AI User role
gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT \
  --member="user:$USER_EMAIL" \
  --role="roles/aiplatform.user"

# Grant BigQuery Data Viewer role
gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT \
  --member="user:$USER_EMAIL" \
  --role="roles/bigquery.dataViewer"

# Grant BigQuery Job User role
gcloud projects add-iam-policy-binding $GOOGLE_CLOUD_PROJECT \
  --member="user:$USER_EMAIL" \
  --role="roles/bigquery.jobUser"
```

---

## Quickstart Setup & Run

Copy and run the following commands in your bash terminal to install the workspace package, seed the sandbox database, run the FastAPI server, and test the dynamic discovery query:

```bash
# 1. Install current package in editable mode
pip install -e .

# 2. Seed the sandbox database in BigQuery
python seed_mock_data.py

# 3. Choose your execution interface:

# OPTION A: Start the FastAPI API Server
PYTHONUNBUFFERED=1 GOOGLE_CLOUD_PROJECT=$GOOGLE_CLOUD_PROJECT uvicorn main:app --reload --host 0.0.0.0 --port 8080

# OPTION B: Start the interactive ADK Web UI
# (Note: Use absolute path `~/Library/Python/3.11/bin/adk web .` if `adk` is not in your PATH)
GOOGLE_CLOUD_PROJECT=$GOOGLE_CLOUD_PROJECT adk web .
```

### Interacting and Testing the Agents

Depending on the option you selected in Step 3:

#### If running the FastAPI Server (Option A):
Open a new terminal and send a POST request:
```bash
curl -X POST "http://localhost:8080/query" \
     -H "Content-Type: application/json" \
     -d '{"user_input": "What is the total revenue for transactions that were delayed in Q1?"}'
```

#### If running the ADK Web UI (Option B):
1. Open your browser and navigate to the local URL printed in your terminal (typically `http://127.0.0.1:8000`).
2. Select your agent from the list.
3. Submit your query directly in the chat box: *"What is the total revenue for transactions that were delayed in Q1?"*
4. Watch the agent plan, call MCP tools, and discover schemas in real time.

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

