# %%
import chromadb
import sqlite3
import logging
from pprint import pprint

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

DB_FILE = "data/sqlite/python.db"
CHROMA_DIR = "./data/chroma/"
COLLECTION_NAME = "python_wiki"

logger.info("getting documents from sqlite")
try:
    with sqlite3.connect(DB_FILE) as conn:
        documents = conn.execute("SELECT * from Pythons").fetchall()
    logger.info(f"Got documents, example document:\n{documents[0]}")
except sqlite3.Error as e:
    logger.error("SQL error, stopping: ", e)
    exit()

logger.info("starting Chroma client")
client = chromadb.PersistentClient(CHROMA_DIR)

logger.info("creating Chroma collection")
collection = client.create_collection(name=COLLECTION_NAME)

logger.info("Adding Data to Chroma collection")
collection.add(
    ids=[str(d[0]) for d in documents],
    documents=[" ".join(d[1:]) for d in documents],
    metadatas=[{"section": d[1]} for d in documents],
)

# %%
## testinmport chromadb
from pprint import pprint

CHROMA_DIR = "./data/chroma/"
COLLECTION_NAME = "python_wiki"
client = chromadb.PersistentClient(CHROMA_DIR)
collection = client.get_collection(COLLECTION_NAME)

results = collection.query(
    query_texts=["python taxonomy"],
    n_results=5,
    include=["documents", "distances"],
)
results["distances"] = results["distances"][0]  # some cleanup
results["documents"] = results["documents"][0]  # some cleanup
# filtering
pprint(
    [(x, y) for (x, y) in zip(results["distances"], results["documents"]) if x < 0.9]
)
# %%
# %%
# %%
# %%
# %%
