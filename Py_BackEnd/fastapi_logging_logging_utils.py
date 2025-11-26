from contextvars import ContextVar
import logging

# create an async variable to store the id
context_id: ContextVar[str] = ContextVar("context_id", default="123")

def create_custom_filter_logger():
    class ContextIDFilter(logging.Filter):
        """
        Injects the local context_id variable from the FastAPI middleware into the log record
        """
        def filter(self, record: logging.LogRecord) -> bool:
            record.id = context_id.get()
            return True

    logger = logging.getLogger(__name__)
    # add the id into the format string
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s [%(levelname)s] %(id)s: %(message)s"
    )
    logger.addFilter(ContextIDFilter())
    return logger

from fastapi import Response
from starlette.middleware.base import BaseHTTPMiddleware
from uuid import uuid4

# middleware to catch all http requests and set a local id
class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request : Request, call_next)
        request_id = str(uuid4())
        context_id.set(request_id[:4])
        response: Response = await call_next(request)
        return response
