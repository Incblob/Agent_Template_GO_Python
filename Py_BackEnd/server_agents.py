from typing import Dict, Optional, List, Tuple
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from http import HTTPStatus
import fastapi_logging_utils as log_utils
from requests import post
import logging

from smolagents import (
    tool,
    CodeAgent,
    InferenceClientModel,
    DuckDuckGoSearchTool,
    VisitWebpageTool,
    FinalAnswerTool,
    WikipediaSearchTool,
)

## SETUP LOGGING w. injected contextVar log ids
logger = log_utils.create_custom_filter_logger("agents")


## SETUP smolagents manager & data agent
@tool
def rag_data_request(
    query: str, n_documents: Optional[int], distance_threshold: Optional[float]
) -> List[Tuple[str, float]]:
    """This function queries a vector database for relevant entries for the query.
    It sends a POST request containing the query
    and optionally the number of documents
    and the maximum distance_threshold for similarity to the query to return.

    Args:
        query (str): The query for the database
        n_documents (Optional[int]):  the number of documents to request. Should be at least 1
        distance_threshold (Optional[float]): the maximum distance to the query. A minimum value of at around 0.8 to 0.9 is recommended.
            The threshold can be increased to return only the most relevant documents.
            If none are returned, the threshold was either set too high or there are no relevant documents

    Returns: A list of Tuples containing the relevant document as well as the distance to the query. The higher the distance, the less relevant the information.
    """
    req_body = {
        "query": query,
        "n_documents": n_documents,
        "distance_threshold": distance_threshold,
    }
    return post("http://127.0.0.1:9000/get_documents", json=req_body)


rag_agent = CodeAgent(
    model=InferenceClientModel(),
    tools=[rag_data_request],
    name="rag_agent",
    description="An agent which queries a vector database for relevant information",
    verbosity_level=0,
    max_steps=2,
)

web_agent = CodeAgent(
    model=InferenceClientModel(),
    tools=[DuckDuckGoSearchTool(), VisitWebpageTool(), WikipediaSearchTool()],
    name="web_agent",
    description="An agent which searches the internet for information on a query",
    verbosity_level=0,
    max_steps=4,
)

manager_agent = CodeAgent(
    model=InferenceClientModel(),
    managed_agents=[rag_agent, web_agent],
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


class AgentRequest(BaseModel):
    query: str


@app.post("/query_agent")
async def agent_query(request: AgentRequest) -> str:
    """
    makes a query to the manager agent
    """
    logger.debug(f"Agent Request received for query {request.query}")
    return manager_agent.run(request.query, return_full_result=False)


if __name__ == "__main__":
    uvicorn.run("server_agents:app", host="127.0.0.1", port=8000, reload=True)
