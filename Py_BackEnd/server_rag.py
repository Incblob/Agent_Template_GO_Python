from contextlib import asynccontextmanager
from typing import Dict, List

# import uvicorn
from fastapi import FastAPI, Response
import chromadb
from http import HTTPStatus
from pydantic import BaseModel
import fastapi_logging_utils as log_utils
import logging


## APP
# create logger and init db w. lifetime event
@asynccontextmanager
async def lifespan(app: FastAPI):
    log_name = "agents_server_logger"
    if log_name in logging.Logger.manager.loggerDict.keys():
        print(
            "logger already in loggers",
        )
    global logger
    logger = log_utils.create_custom_filter_logger(log_name, level=logging.DEBUG)

    ## DB CONFIG
    CHROMA_DIR = "./data/chroma/"
    COLLECTION_NAME = "python_wiki"
    logger.info("starting Chroma client")

    global collection

    client = chromadb.PersistentClient(CHROMA_DIR)
    collection = client.get_collection(COLLECTION_NAME)
    logger.info("chromadb ready")

    yield


app = FastAPI(lifespan=lifespan)

# add custom logging middleware that uses a ContextVar for per-request log ids
app.add_middleware(log_utils.LoggingMiddleware)


@app.get("/health")
async def health():
    return HTTPStatus.OK


class RagRequest(BaseModel):
    query: str
    n_results: int = 2
    distance_threshold: float = 1.1


def filter_documents(documents: chromadb.QueryResult, distance_threshold: float):
    # we are assuming a single query, so the Documents and distances are lists containing one list
    filtered: List[Dict[str, float | str]] = [
        {"document": str(x), "distance": y}
        for (x, y) in zip(documents["documents"][0], documents["distances"][0])  # type: ignore
        if y < distance_threshold
    ]
    return filtered


@app.post("/get_documents")
async def rag_request(request: RagRequest):
    """
    returns the relevant documents for a query
    """
    logger.debug(f"Document Request received for query {request.query}")

    try:
        documents = collection.query(
            query_texts=[request.query],
            n_results=request.n_results,
            include=["documents", "distances"],
        )
    except ValueError as e:  # query should normally only return a ValueError
        logger.warning(f"ValueError in collection: \n{e}")
        return Response(
            content=f"Error {e} in DB", status_code=HTTPStatus.UNPROCESSABLE_CONTENT
        )

    return filter_documents(documents, request.distance_threshold)


# if __name__ == "__main__":
#     uvicorn.run("server_rag:app", host="127.0.0.1", port=9000, reload=True)
