import json
from typing import Any, Optional
import redis
from app.core.config import settings
from app.core.logging import StructuredLogger

class RedisCache:
    """
    Resilient Redis Caching wrapper. Falls back gracefully to database/live execution
    if Redis caching is disabled or the server is offline.
    """
    _client: Optional[redis.Redis] = None

    @classmethod
    def get_client(cls) -> Optional[redis.Redis]:
        if not settings.ENABLE_REDIS_CACHE:
            return None
        
        if cls._client is None:
            try:
                cls._client = redis.Redis.from_url(
                    settings.REDIS_URL, 
                    socket_connect_timeout=2.0,
                    socket_timeout=2.0
                )
                # Test connection availability
                cls._client.ping()
                StructuredLogger.info("Successfully established connection to Redis cache pool.")
            except Exception as e:
                StructuredLogger.warning(f"Redis cache pool unavailable. Falling back: {str(e)}")
                cls._client = None
                
        return cls._client

    @classmethod
    def get(cls, key: str) -> Optional[Any]:
        client = cls.get_client()
        if not client:
            return None
        try:
            val = client.get(key)
            if val:
                return json.loads(val.decode("utf-8"))
        except Exception as e:
            StructuredLogger.warning(f"Error reading from Redis cache (key={key}): {str(e)}")
            cls._client = None  # Reset client to retry connection on next call
        return None

    @classmethod
    def set(cls, key: str, value: Any, expire_seconds: int = 300) -> None:
        client = cls.get_client()
        if not client:
            return
        try:
            serialized = json.dumps(value)
            client.setex(key, expire_seconds, serialized)
        except Exception as e:
            StructuredLogger.warning(f"Error writing to Redis cache (key={key}): {str(e)}")
            cls._client = None  # Reset client
