import logging
from typing import Annotated
import uvicorn
from fastapi import FastAPI, Response
from pydantic import AfterValidator, BaseModel, Field
from http import HTTPStatus
from fastapi_logging_utils import create_custom_filter_logger, LoggingMiddleware
from logging import DEBUG, INFO
from contextlib import asynccontextmanager
from smolagent_class import create_agent_class


# create logger w. lifetime event
@asynccontextmanager
async def lifespan(app: FastAPI):
    log_name = "agents_server_logger"
    if log_name in logging.Logger.manager.loggerDict.keys():
        logging.info("logger already in loggers", )
    global logger
    logger = create_custom_filter_logger(log_name, level=DEBUG)

    global Agents
    Agents = create_agent_class()

    yield


#data val & models

def val_min_length(query: str)-> str:
    if len(query.split(" "))<3:
        raise ValueError(f"Query '{query}' is smaller than 4 words, please elaborate")
    return query

class AgentRequest(BaseModel):
    query: Annotated[str, AfterValidator(val_min_length)] = Field(min_length=10)


## APP

app = FastAPI(lifespan = lifespan)

# add custom logging middleware that uses a ContextVar for per-request log ids
app.add_middleware(LoggingMiddleware)

## Endpoints

@app.get("/health")
async def health():
    return HTTPStatus.OK

@app.post("/query_agent")
async def agent_query(request: AgentRequest) -> Response:
    """
    makes a query to the manager agent
    """
    logger.debug(f"Agent Request received")
    return Response(Agents.run(request.query,  return_full_result=False), status_code=HTTPStatus.OK)
    # return document_request(request.query)


if __name__ == "__main__":
    uvicorn.run("server_agents:app", host="127.0.0.1", port=8000, reload=True)
