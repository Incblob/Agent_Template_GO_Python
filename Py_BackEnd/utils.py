from typing import Dict
from fastapi import Response
from requests import HTTPError, RequestException, Timeout, post, ConnectionError
from requests import Response as PostResponse
from http import HTTPStatus
from logging import getLogger
from os import getenv

logger = getLogger("agents_server_logger")

DB_HOST = getenv("DB_HOST")
assert DB_HOST
DB_PORT = getenv("DB_PORT")
assert DB_PORT

DB_PATH: str = (
    "http://" + DB_HOST + ":" + DB_PORT + "/get_documents"
)  # use the container id for connecting from container to container


def document_request(
    query: str, n_documents: int = 2, distance_threshold: float = 1
) -> Response:
    """This function queries a vector database for relevant entries for the query.
    It sends a POST request containing the query
    and optionally the number of documents
    and the maximum distance_threshold for similarity to the query to return.
    The output might be improved by including synonyms for key words.

    Args:
        query (str): The query for the database
        n_documents (Optional[int]):  the number of documents to request. Should be at least 1
        distance_threshold (Optional[float]): the maximum distance to the query. A minimum value of at around 0.8 to 0.9 is recommended.
            The threshold can be increased to return only the most relevant documents.
            If none are returned, the threshold was either set too high or there are no relevant documents

    Returns: A list of Tuples containing the relevant document as well as the distance to the query. The higher the distance, the less relevant the information.
    """
    req_body: Dict[str, str | int | float] = {
        "query": query,
        "n_documents": n_documents,
        "distance_threshold": distance_threshold,
    }

    try:
        response: PostResponse = post(
            DB_PATH,
            # "http://db:9000/get_documents",  # use the container id for connecting from container to container
            json=req_body,
            headers={"Content-type": "application/json"},
            timeout=10,
        )
        response.raise_for_status()
        return Response(content=response.content, status_code=response.status_code)
    except ConnectionError as e:
        logger.critical("❗ Vector Database not reachable!\n" + str(e))
        return Response(
            content="Vector DB is currently unavailable",
            status_code=HTTPStatus.SERVICE_UNAVAILABLE,
        )
    except Timeout as e:
        logger.critical("❗ Vector Database request timed out!\n" + str(e))
        return Response(
            content="Vector DB request timed out",
            status_code=HTTPStatus.GATEWAY_TIMEOUT,
        )
    except HTTPError as e:
        logger.critical(f"❗ HTTP Error: {e.response.status_code}\n" + str(e))
        return Response(
            content=f"Error in DB Response:\n{e.response.content}",
            status_code=e.response.status_code,
        )
    except RequestException as e:
        logger.critical("❗ Request failed: " + str(e))
        return Response(content=str(e), status_code=HTTPStatus.INTERNAL_SERVER_ERROR)
