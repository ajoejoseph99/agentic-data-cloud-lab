import os
import google.auth
import google.auth.transport.requests
from google.adk.agents.llm_agent import Agent
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPConnectionParams
from google.adk.tools.mcp_tool.mcp_toolset import McpToolset

# Dynamically resolve Project ID from the environment
gcp_project = os.environ.get("GOOGLE_CLOUD_PROJECT")
if not gcp_project:
    raise ValueError("GOOGLE_CLOUD_PROJECT environment variable is missing.")

# Tell the Google GenAI SDK to route through Vertex AI (not Gemini API)
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = "1"
os.environ["GOOGLE_CLOUD_LOCATION"] = "us-central1"

# Fetch ambient Google Cloud OAuth2 credentials
credentials, project_id = google.auth.default(
    scopes=["https://www.googleapis.com/auth/bigquery", "https://www.googleapis.com/auth/cloud-platform"]
)
credentials.refresh(google.auth.transport.requests.Request())

# Step 1: Equip the Agent with an Enterprise MCP Tool (with Auth Headers)
bq_toolset = McpToolset(
    connection_params=StreamableHTTPConnectionParams(
        url="https://bigquery.googleapis.com/mcp",
        headers={
            "Authorization": f"Bearer {credentials.token}",
            "x-goog-user-project": gcp_project,
            "Content-Type": "application/json"
        }
    )
)

# Step 2: Define the legacy Root Data Agent (kept for backward compatibility or direct testing)
root_agent = Agent(
    model="gemini-2.5-flash",
    name="enterprise_data_agent",
    instruction=f"""Act as an enterprise data intelligence assistant. 
    You have read-only access to corporate database catalogs strictly via the tools provided in your 'tools' list.
    Your primary sandbox environment (GCP Project) is '{gcp_project}'.
    
    CRITICAL PROTOCOL:
    1. Do NOT attempt to execute arbitrary Python code or call methods like 'introspect_tools()'.
    2. You are provided with a set of tools in your 'tools' list. When you need to discover schemas or query data, simply invoke these tools directly.
    
    Your job is to assist users by autonomously discovering database schemas, executing queries, and providing direct, human-readable answers. 
    Do not output SQL code as your final response; execute the query via the provided tools, analyze the output, and present the final summary directly to the user.""",
    description="An autonomous agent engineered to dynamically discover, query, and reason over BigQuery warehouses.",
    tools=[bq_toolset]
)