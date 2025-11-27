from contextvars import ContextVar
import logging

# create an async variable to store the id
context_id: ContextVar[str] = ContextVar("context_id", default="NO REQ")


def create_custom_filter_logger(name: str, level: int = logging.INFO):
    class ContextIDFilter(logging.Filter):
        """
        Injects the local context_id variable from the FastAPI middleware into the log record
        """

        def filter(self, record: logging.LogRecord) -> bool:
            setattr(record, "id", context_id.get())
            # record.id = context_id.get()
            return True

    logger = logging.getLogger(name)
    logger.setLevel(level)
    handler = logging.StreamHandler()
    handler.formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(id)s: %(message)s"
    )
    handler.addFilter(ContextIDFilter())
    logger.handlers = []
    logger.addHandler(handler)

    return logger


from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from uuid import uuid4


# middleware to catch all http requests and set a local id
class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid4())
        context_id.set(request_id[:4])
        response: Response = await call_next(request)
        return response
