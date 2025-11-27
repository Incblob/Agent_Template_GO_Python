import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from http import HTTPStatus
import fastapi_logging_logging_utils as log_utils

from smolagents import (
    tool,
    CodeAgent,
    InferenceClientModel,
    DuckDuckGoSearchTool,
    VisitWebpageTool,
    FinalAnswerTool,
)

## SETUP LOGGING w. injected contextVar log ids
logger = log_utils.create_custom_filter_logger("agents")


## SETUP smolagents manager & data agent
@tool
def rag_data_request():
    pass


rag_agent = CodeAgent(
    model=InferenceClientModel(),
    tools=[DuckDuckGoSearchTool(), VisitWebpageTool(), rag_data_request],
    name="rag_agent",
    description="An agent which queries a vector database for relevant information",
    verbosity_level=0,
    max_steps=2,
)

manager_agent = CodeAgent(
    model=InferenceClientModel(),
    managed_agents=[rag_agent],
    tools=[FinalAnswerTool()],
    planning_interval=5,
    verbosity_level=2,
    final_answer_checks=[],
    max_steps=15,
)


## APP
app = FastAPI()
# add custom logging middleware that uses a ContextVar for per-request log ids
app.add_middleware(log_utils.LoggingMiddleware)


@app.get("/health")
async def health():
    return HTTPStatus.OK


class RagRequest(BaseModel):
    query: str
    n_results: int = 5


@app.post("/query_agent")
async def agent_query(request: RagRequest):
    """
    makes a query to the manager agent
    """
    logger.debug(f"Agent Request received for query {request.query}")


if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
