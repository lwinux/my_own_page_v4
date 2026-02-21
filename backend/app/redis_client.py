from redis.asyncio import Redis, ConnectionPool
from app.config import get_settings

_pool: ConnectionPool | None = None


def init_redis_pool() -> None:
    global _pool
    settings = get_settings()
    _pool = ConnectionPool.from_url(
        settings.REDIS_URL,
        decode_responses=True,
        max_connections=20,
    )


def get_pool() -> ConnectionPool:
    if _pool is None:
        raise RuntimeError("Redis pool not initialised. Call init_redis_pool() at startup.")
    return _pool


async def close_redis_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.aclose()
        _pool = None


async def get_redis() -> Redis:
    """FastAPI dependency — yields a Redis client backed by the shared pool."""
    client = Redis(connection_pool=get_pool())
    try:
        yield client
    finally:
        await client.aclose()
