import uuid
import uvicorn
from fastapi import FastAPI, Request, Response
import chromadb
from pydantic import BaseModel
from fastapi_logging_logging_utils import create_custom_filter_logger, LoggingMiddleware

## SETUP LOGGING w. injected contextVar log ids
logger = create_custom_filter_logger()


## DB CONFIG
CHROMA_DIR = "./data/chroma/"
COLLECTION_NAME = "python_wiki"
logger.info("starting Chroma client")
client = chromadb.PersistentClient(CHROMA_DIR)
collection = client.get_collection(COLLECTION_NAME)
logger.info("chromadb ready")


## APP
app = FastAPI()
# add custom logging middleware that uses a ContextVar for per-request log ids
app.add_middleware(LoggingMiddleware)


class RagRequest(BaseModel):
    query: str
    n_results: int = 5


@app.post("/get_documents")
async def rag_request(request: RagRequest):
    """
    returns the relevant documents for a query
    """
    logger.debug(f"Document Request received for query {request.query}")

    return collection.query(
        query_texts=[request.query],
        n_results=request.n_results,
        include=["documents", "distances"],
    )


if __name__ == "__main__":
    uvicorn.run("app:app", host="127.0.0.1", port=9000, reload=True)
