import json
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.middleware.error_handler import IdempotencyViolation
from app.core.config import settings

# In-memory fallback dictionary for when Redis cache is disabled or unavailable
_IN_MEMORY_IDEMPOTENCY_CACHE = {}


class IdempotencyMiddleware(BaseHTTPMiddleware):
    """
    Middleware checking the 'Idempotency-Key' header on mutating requests.
    Uses Redis cache if enabled, falling back to an in-memory dictionary.
    """
    async def dispatch(self, request: Request, call_next) -> Response:
        # Check only mutating requests (POST, PUT, DELETE) containing Idempotency-Key
        if request.method not in ["POST", "PUT", "DELETE"]:
            return await call_next(request)

        idempotency_key = request.headers.get("Idempotency-Key")
        if not idempotency_key:
            return await call_next(request)

        cached_val = None
        if settings.ENABLE_REDIS_CACHE:
            try:
                import redis
                r = redis.Redis.from_url(settings.REDIS_URL)
                val = r.get(f"idempotency:{idempotency_key}")
                if val:
                    cached_val = json.loads(val.decode("utf-8"))
            except Exception:
                pass

        if not cached_val:
            cached_val = _IN_MEMORY_IDEMPOTENCY_CACHE.get(idempotency_key)

        if cached_val:
            if cached_val.get("status") == "processing":
                raise IdempotencyViolation("Duplicate transaction submitted and currently active")
            
            return JSONResponse(
                status_code=cached_val.get("status_code", 200),
                content=cached_val.get("content")
            )

        # Mark as processing
        initial_cache_val = {"status": "processing"}
        if settings.ENABLE_REDIS_CACHE:
            try:
                import redis
                r = redis.Redis.from_url(settings.REDIS_URL)
                r.setex(f"idempotency:{idempotency_key}", 300, json.dumps(initial_cache_val))
            except Exception:
                pass
        _IN_MEMORY_IDEMPOTENCY_CACHE[idempotency_key] = initial_cache_val

        try:
            response = await call_next(request)
            
            # Read and reconstruct response body to avoid consuming the stream permanently
            response_body = b""
            async for chunk in response.body_iterator:
                response_body += chunk
            
            new_response = Response(
                content=response_body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type
            )

            try:
                content_data = json.loads(response_body.decode("utf-8"))
            except Exception:
                content_data = response_body.decode("utf-8")

            completed_cache_val = {
                "status": "completed",
                "status_code": response.status_code,
                "content": content_data
            }

            if settings.ENABLE_REDIS_CACHE:
                try:
                    import redis
                    r = redis.Redis.from_url(settings.REDIS_URL)
                    r.setex(f"idempotency:{idempotency_key}", 86400, json.dumps(completed_cache_val))
                except Exception:
                    pass
            _IN_MEMORY_IDEMPOTENCY_CACHE[idempotency_key] = completed_cache_val

            return new_response

        except Exception as e:
            # Clean cache on failure so the request can be retried
            if settings.ENABLE_REDIS_CACHE:
                try:
                    import redis
                    r = redis.Redis.from_url(settings.REDIS_URL)
                    r.delete(f"idempotency:{idempotency_key}")
                except Exception:
                    pass
            _IN_MEMORY_IDEMPOTENCY_CACHE.pop(idempotency_key, None)
            raise e
