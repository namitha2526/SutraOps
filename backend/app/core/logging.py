import json
import logging
import time
import uuid
from contextvars import ContextVar
from typing import Any, Dict, Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

# Context Variables for Request Tracing and Tenant Identification
correlation_id_ctx: ContextVar[str] = ContextVar("correlation_id", default="")
organization_id_ctx: ContextVar[str] = ContextVar("organization_id", default="")
user_id_ctx: ContextVar[str] = ContextVar("user_id", default="")

# Logging Setup
logger = logging.getLogger("nexusflow")
logger.setLevel(logging.INFO)

# Stream handler to stdout
handler = logging.StreamHandler()


class JsonFormatter(logging.Formatter):
    """
    Format logs into a structured JSON string containing current request context variables.
    """
    def format(self, record: logging.LogRecord) -> str:
        # Retrieve contextvars safely
        cid = correlation_id_ctx.get()
        oid = organization_id_ctx.get()
        uid = user_id_ctx.get()

        log_data: Dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "module": record.module,
            "line": record.lineno,
            "correlation_id": cid,
            "organization_id": oid,
            "user_id": uid,
        }

        # Embed extra context properties if present
        if hasattr(record, "extra_attrs") and isinstance(record.extra_attrs, dict):
            log_data.update(record.extra_attrs)

        return json.dumps(log_data)


handler.setFormatter(JsonFormatter())
logger.addHandler(handler)
logger.propagate = False


def get_logger():
    return logger


class StructuredLogger:
    @staticmethod
    def info(msg: str, **kwargs):
        extra = {"extra_attrs": kwargs}
        logger.info(msg, extra=extra)

    @staticmethod
    def error(msg: str, **kwargs):
        extra = {"extra_attrs": kwargs}
        logger.error(msg, extra=extra)

    @staticmethod
    def warning(msg: str, **kwargs):
        extra = {"extra_attrs": kwargs}
        logger.warning(msg, extra=extra)

    @staticmethod
    def debug(msg: str, **kwargs):
        extra = {"extra_attrs": kwargs}
        logger.debug(msg, extra=extra)


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """
    HTTP Middleware checking X-Correlation-ID headers, generating tracers if missing,
    and binding context variables to the request cycle thread.
    """
    async def dispatch(self, request: Request, call_next) -> Response:
        # Check header
        correlation_id = request.headers.get("X-Correlation-ID")
        if not correlation_id:
            correlation_id = str(uuid.uuid4())

        # Bind token
        token_cid = correlation_id_ctx.set(correlation_id)
        
        # Capture optional organization ID from header for soft multi-tenancy
        org_id = request.headers.get("X-Organization-ID", "")
        token_oid = organization_id_ctx.set(org_id)

        start_time = time.time()
        StructuredLogger.info(
            f"Request Started: {request.method} {request.url.path}",
            method=request.method,
            path=request.url.path,
            ip=request.client.host if request.client else "unknown"
        )

        try:
            response: Response = await call_next(request)
            process_time = time.time() - start_time
            response.headers["X-Correlation-ID"] = correlation_id
            StructuredLogger.info(
                f"Request Finished: {request.method} {request.url.path} - Status {response.status_code}",
                status_code=response.status_code,
                duration=f"{process_time:.4f}s"
            )
            return response
        except Exception as e:
            process_time = time.time() - start_time
            StructuredLogger.error(
                f"Unhandled Exception: {request.method} {request.url.path} - Error: {str(e)}",
                error=str(e),
                duration=f"{process_time:.4f}s"
            )
            # Re-raise to let error handling middleware map this correctly
            raise e
        finally:
            # Clear context vars
            correlation_id_ctx.reset(token_cid)
            organization_id_ctx.reset(token_oid)
