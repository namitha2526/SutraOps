from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from jose import jwt, JWTError
from app.core.config import settings
from app.core.logging import organization_id_ctx, StructuredLogger


class TenantIsolationMiddleware(BaseHTTPMiddleware):
    """
    Middleware that intercepts incoming requests, parses the organizational context
    (either from header or Bearer Token claim), and binds it to contextvars.
    """
    async def dispatch(self, request: Request, call_next) -> Response:
        org_id = ""

        # 1. First check dedicated Header
        header_org = request.headers.get("X-Organization-ID")
        if header_org:
            org_id = header_org

        # 2. If missing, check JWT Authorization Header to extract org claim
        if not org_id:
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
                try:
                    payload = jwt.decode(
                        token,
                        settings.SECRET_KEY,
                        algorithms=["HS256"]
                    )
                    org_id = payload.get("org_id", "")
                except JWTError:
                    # Invalid token will be properly handled by Auth Dependency Injection layer later,
                    # here we fail gracefully and proceed.
                    pass

        # Bind the validated organization context token to current contextvar thread
        token_oid = organization_id_ctx.set(org_id)

        try:
            response = await call_next(request)
            return response
        finally:
            # Revert the context variable post-request resolution to avoid thread leaking
            organization_id_ctx.reset(token_oid)
