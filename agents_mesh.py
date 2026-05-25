import asyncio
import uuid
from unittest.mock import MagicMock
from google.genai import types
from google.adk.agents.llm_agent import Agent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.agents.run_config import RunConfig
from google.adk.agents.context import Context
from google.adk.sessions.session import Session
from google.cloud import bigquery
from enterprise_agent.agent import bq_toolset, gcp_project

# THE DEFINITIVE FIX: Explicitly set response_modalities.
# The ADK Vertex AI routing explicitly reads this property. If omitted,
# it resolves to None internally, causing the crash.
agent_config = types.GenerateContentConfig(
    temperature=0.1,
    response_modalities=["TEXT"] 
)

# Step 1: The Planner Agent
planner_agent = Agent(
    model="gemini-2.5-flash",
    name="planner_agent",
    instruction=f"""You are a Strategic Data Planner for GCP project '{gcp_project}'. 
    Your goal is to analyze a user's natural language request and formulate a precise, 
    step-by-step execution plan to discover the schema and fetch the necessary data from BigQuery.
    
    Do NOT assume dataset, table, or schema names. Instead, formulate a plan that instructs the executor agent to:
    1. List the datasets in project '{gcp_project}' to find relevant datasets.
    2. List the tables in the chosen dataset to find the target data table.
    3. Get metadata info for the target table to understand its columns and schema.
    4. Execute a read-only SQL query on the discovered table to retrieve the required data.
    
    Do NOT write SQL. Do NOT execute tools.
    Only output a clear list of schema discovery and querying steps that an executor agent should take.""",
    generate_content_config=agent_config
)

# Step 2: The Executor Agent
executor_agent = Agent(
    model="gemini-2.5-flash",
    name="executor_agent",
    instruction=f"""You are a Data Operations Executor operating in GCP project '{gcp_project}'.
    You will receive a plan from the Planner Agent. Use your provided tools to securely access BigQuery.
    
    CRITICAL PROTOCOL:
    1. Do NOT assume database, dataset, or table names. You must discover them step-by-step using your tools.
    2. Every tool in your 'tools' list (such as `list_dataset_ids`, `list_table_ids`, `get_table_info`, and `execute_sql_readonly`) requires the `projectId` parameter. You MUST set `projectId` to '{gcp_project}' for every single tool call.
    3. Step-by-step: First list datasets, locate the relevant sandbox dataset, list the tables in it, check table schemas, and run a read-only query on the discovered table.
    4. Compile the results from your tool executions into a clear, business-ready summary. Never show SQL to the user in your final response.""",
    tools=[bq_toolset],
    generate_content_config=agent_config
)

async def execute_adk_agent(agent: Agent, text: str) -> str:
    """
    Executes the ADK 2.1+ Agent natively via the async stream,
    using MagicMock for nested context objects to satisfy strict state validation.
    """
    
    # 1. Enforce the config dynamically right before execution as a safety net
    if getattr(agent, 'generate_content_config', None) is None:
        agent.generate_content_config = agent_config
    else:
        agent.generate_content_config.response_modalities = ["TEXT"]
    
    # 2. Synthesize the Session object
    session = Session(
        id=str(uuid.uuid4()),
        app_name="agentic_data_cloud",
        user_id="user",
        state={},
        events=[]
    )
    
    # 3. Synthesize the Pydantic InvocationContext
    inv_ctx = InvocationContext.model_construct(
        session_service=None,
        session=session,
        invocation_id=str(uuid.uuid4()),
        run_config=RunConfig(response_modalities=["TEXT"])
    )
    
    # 4. Synthesize the top-level SDK Context
    ctx = Context(inv_ctx, node_path=agent.name)
    
    # THE ULTIMATE SAFEGUARD: Bind the config directly to the context 
    # to intercept any internal `getattr(ctx, 'config', None)` calls.
    ctx.config = agent_config
    ctx.generate_content_config = agent_config
    
    final_output = ""
    
    async for event in agent.run(ctx=ctx, node_input=text):
        print(f"[{agent.name}] EVENT: {type(event).__name__} - {str(event)[:300]}")
        if hasattr(event, 'content') and event.content is not None:
            if isinstance(event.content, str):
                final_output += event.content
            elif hasattr(event.content, 'text') and event.content.text is not None:
                final_output += event.content.text
            elif hasattr(event.content, 'parts') and event.content.parts is not None:
                for part in event.content.parts:
                    if hasattr(part, 'text') and part.text is not None:
                        final_output += part.text
        elif hasattr(event, 'text') and event.text is not None:
            final_output += event.text
            
    return final_output.strip()

async def execute_adk_agent_with_retry(agent: Agent, text: str, max_retries: int = 5) -> str:
    """
    Executes the ADK agent with a backoff retry mechanism when hitting 429/RESOURCE_EXHAUSTED errors.
    """
    for attempt in range(max_retries):
        try:
            return await execute_adk_agent(agent, text)
        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                sleep_time = (attempt + 1) * 15
                print(f"⚠️ Rate limited (429 RESOURCE_EXHAUSTED). Waiting {sleep_time} seconds before retrying... (Attempt {attempt+1}/{max_retries})")
                await asyncio.sleep(sleep_time)
            else:
                raise e
    raise RuntimeError("Max retries exceeded due to Vertex AI rate limits.")

async def get_agent_response(user_query: str) -> str:
    """
    Fully Async Orchestrator: Planner defines the strategy, Executor runs the tools.
    """
    print(f"🔄 Routing query to Planner Agent...")
    execution_plan = await execute_adk_agent_with_retry(
        planner_agent, 
        f"Formulate a plan for this user query: {user_query}"
    )
    
    print(f"⚙️ Routing plan to Executor Agent...")
    final_response = await execute_adk_agent_with_retry(
        executor_agent, 
        f"Original Query: {user_query}\n\nExecution Plan:\n{execution_plan}"
    )
    
    return final_response