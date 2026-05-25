from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from agents_mesh import get_agent_response
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Agentic Data Cloud API",
    description="Secure, multi-agent REST API powered by Google ADK and MCP",
    version="1.0.0"
)

# Pydantic schema for the request payload
class QueryRequest(BaseModel):
    user_input: str

@app.post("/query")
async def handle_query(request: QueryRequest):
    logger.info(f"Received query: {request.user_input}")
    try:
        # AWAIT the async mesh!
        result = await get_agent_response(request.user_input)
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"Agent Mesh Execution Failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal agent execution failed.")

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "agentic-data-mesh"}
