from contextvars import ContextVar
import logging

# create an async variable to store the id
context_id: ContextVar[str] = ContextVar("context_id", default="NoID")

def create_custom_filter_logger(name: str, level: int = logging.INFO):
    if name in logging.Logger.manager.loggerDict.keys():
        logging.warning(
            f" 💬 Logger name '{name}' already exists, skipping creating new logger"
        )
        return logging.getLogger(name)
    class ContextIDFilter(logging.Filter) :
        """
        Injects the local context_id variable from the FastAPI middleware into the log record
        """

        def filter(self, record: logging.LogRecord) -> bool:
            setattr(record, "id", context_id.get())
            return True

    logger = logging.getLogger(name)
    logger.setLevel(level)
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter(
        "💬 %(asctime)s [%(levelname)s] %(id)s: %(message)s"
    ))
    handler.addFilter(ContextIDFilter())  # remember to instantiate the class
    logger.handlers = []
    logger.addHandler(handler)

    logger.debug(f"💬 created logger {name}")

    return logger


from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from uuid import uuid4

# middleware to catch all http requests and set a local id
# we could also create a router with base functionality for logging and health endpoints,
# but that's a bit over the top for this simple example.
class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid4())
        context_id.set(request_id[:4])
        response: Response = await call_next(request)
        return response
