# Agentic Microservices Example

Contains a series of python programms that emulate a microservice architecture for implementing Agentic AI with RAG.

Two scripts [setup_Chroma_db.py](./setup_Chroma_db.py) and [setup_sqlite_db.py](./setup_sqlite_db.py) are used to populate on-file databases.

The files starting with "server" start the microservice servers.
Of these:

- [server_agents.py](./server_agents.py) manages the Agentic AI
- [server_rag.py](./server_rag.py) runs queries against the Chroma vector db

[fastapi_logging_utils.py](./fastapi_logging_utils.py) contains utilities for injecting unique ids into requests coming into fastapi endpoints. (see [Explanation](#request-id-injection))

[utils.py](./utils.py) contains the function to request data from the vector db.

Main libraries:

- FastAPI
- uvicorn
- Chromadb
- sqlite3
- smolagents


## DB populating

This emulates injesting data from a existing db to populate a vector db for RAG queries

1. The [SQLite script](./setup_sqlite_db.py) reads in text file in the data/python_wiki folder and uploads them into an on-file db in *data/sqlite*
2. The [Chroma script](./setup_Chroma_db.py) queries the SQLite db and encodes the contents onto an on-file db in */data/chroma*

## Servers

### Agentic AI

Uses [smolagents](https://github.com/huggingface/smolagents) for agentic AI.

Agents:
- A manager Agent which calls the *RAG agent* and summarises the results
- RAG agent which calls the *RAG server* to query the vector database and summarize the results

### 'RAG' Server

responds to queries to the vector db

## Request ID injection
Using a ContextVar as an ID, we can use a custom Filter in the logging handler to add an ID to the log record.

Then, we can add a middleware function to the FastAPI app which changes the ID(ContextVar) for each HTTP request.

Since ContextVars are isolated to each async process, every log for a given request will contain the same ID. This can be further customized in formatting (such as adding details from the request itself), but in this case a minimal example was used.
