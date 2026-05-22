from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logging import StructuredLogger, correlation_id_ctx
from sqlalchemy.orm.exc import StaleDataError


# =====================================================================
# Domain Exception Classes
# =====================================================================

class NexusFlowException(Exception):
    """Base exception class for all domain errors."""
    def __init__(self, message: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class TenantAccessDenied(NexusFlowException):
    def __init__(self, message: str = "Access Denied: Cross-tenant data leak blocked"):
        super().__init__(message, status.HTTP_403_FORBIDDEN)


class PermissionDenied(NexusFlowException):
    def __init__(self, message: str = "Forbidden: Insufficient privileges"):
        super().__init__(message, status.HTTP_403_FORBIDDEN)


class ResourceNotFound(NexusFlowException):
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status.HTTP_404_NOT_FOUND)


class RulesEngineError(NexusFlowException):
    def __init__(self, message: str = "Rule evaluation processing error"):
        super().__init__(message, status.HTTP_422_UNPROCESSABLE_ENTITY)


class ConcurrencyConflict(NexusFlowException):
    def __init__(self, message: str = "Stale State: Record updated by another process. Please reload."):
        super().__init__(message, status.HTTP_409_CONFLICT)


class IdempotencyViolation(NexusFlowException):
    def __init__(self, message: str = "Duplicate transaction submitted and currently active"):
        super().__init__(message, status.HTTP_409_CONFLICT)


# =====================================================================
# Exception Handling Middleware
# =====================================================================

class CentralizedErrorHandlerMiddleware(BaseHTTPMiddleware):
    """
    Middleware intercepting unhandled and domain exceptions, returning consistent structured JSON.
    """
    async def dispatch(self, request: Request, call_next) -> Response:
        try:
            return await call_next(request)
        except StaleDataError as e:
            # Map SQLAlchemy stale data error automatically to ConcurrencyConflict
            StructuredLogger.warning(
                "SQLAlchemy StaleDataError intercepted: Concurrent execution blocked",
                path=request.url.path
            )
            return self._build_error_response(
                status_code=status.HTTP_409_CONFLICT,
                title="Stale State Conflict",
                detail="The record has been modified by another process. Please refresh the page and try again."
            )
        except NexusFlowException as e:
            StructuredLogger.warning(
                f"Domain Exception Intercepted: {e.message}",
                path=request.url.path,
                status_code=e.status_code
            )
            return self._build_error_response(
                status_code=e.status_code,
                title=e.__class__.__name__,
                detail=e.message
            )
        except Exception as e:
            StructuredLogger.error(
                f"Unhandled System Exception: {str(e)}",
                path=request.url.path,
                error_class=e.__class__.__name__
            )
            return self._build_error_response(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                title="Internal Server Error",
                detail="An unexpected error occurred. Please contact system administrators."
            )

    def _build_error_response(self, status_code: int, title: str, detail: str) -> JSONResponse:
        cid = correlation_id_ctx.get()
        payload = {
            "title": title,
            "status": status_code,
            "detail": detail,
            "correlation_id": cid,
        }
        return JSONResponse(
            status_code=status_code,
            content=payload
        )
