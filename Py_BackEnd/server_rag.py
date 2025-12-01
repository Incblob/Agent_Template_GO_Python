from typing import List, Optional, Tuple
import uvicorn
from fastapi import FastAPI
import chromadb
from http import HTTPStatus
from pydantic import BaseModel
import fastapi_logging_utils as log_utils
import logging

## SETUP LOGGING w. injected contextVar log ids
logger = log_utils.create_custom_filter_logger("rag")

## APP
app = FastAPI()

# add custom logging middleware that uses a ContextVar for per-request log ids
app.add_middleware(log_utils.LoggingMiddleware)


## DB CONFIG
CHROMA_DIR = "./data/chroma/"
COLLECTION_NAME = "python_wiki"
logger.info("starting Chroma client")
client = chromadb.PersistentClient(CHROMA_DIR)
collection = client.get_collection(COLLECTION_NAME)
logger.info("chromadb ready")


@app.get("/health")
async def health():
    logger.info("id test")
    return HTTPStatus.OK


class RagRequest(BaseModel):
    query: str
    n_results: int = 2
    distance_threshold: float = 1.1


def filter_documents(
    documents: chromadb.QueryResult, distance_threshold: float
) -> List[Tuple[chromadb.Documents, float]]:
    # we are assuming a single query, so the Documents and distances are lists containing one list
    filtered = [
        (x, y)
        for (x, y) in zip(documents["documents"][0], documents["distances"][0])
        if y < distance_threshold
    ]
    return filtered


@app.post("/get_documents")
async def rag_request(request: RagRequest):
    """
    returns the relevant documents for a query
    """
    logger.debug(f"Document Request received for query {request.query}")

    documents = collection.query(
        query_texts=[request.query],
        n_results=request.n_results,
        include=["documents", "distances"],
    )

    return filter_documents(documents, request.distance_threshold)


if __name__ == "__main__":
    uvicorn.run("server_rag:app", host="127.0.0.1", port=9000, reload=True)
