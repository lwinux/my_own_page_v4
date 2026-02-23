"""
Test configuration.

Tests use an in-memory SQLite database (via aiosqlite).
JSONB is swapped for JSON so the models remain compatible.
Redis is fully mocked.

Run: pytest tests/
"""
import json
import asyncio
from typing import AsyncGenerator
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import JSON, event
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

# Patch JSONB → JSON before importing models
from sqlalchemy.dialects.postgresql import JSONB

JSONB.__init_subclass__ = lambda *a, **kw: None  # type: ignore[assignment]
_orig_jsonb_type_expression = getattr(JSONB, "result_processor", None)


# Monkeypatch: replace JSONB with JSON in SQLite context
import sqlalchemy.dialects.postgresql as pg_dialect  # noqa: E402

pg_dialect.JSONB = JSON  # type: ignore[attr-defined]

# Now safe to import app modules
from app.database import Base, get_session_factory  # noqa: E402
from app.dependencies import get_db, get_current_user  # noqa: E402
from app.redis_client import get_redis  # noqa: E402
from app.main import app  # noqa: E402
from app.models.user import User  # noqa: E402
from app.utils.security import hash_password, create_access_token  # noqa: E402


TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    engine = create_async_engine(
        TEST_DB_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db(test_engine) -> AsyncGenerator[AsyncSession, None]:
    factory = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session
        await session.rollback()


@pytest.fixture
def mock_redis():
    store: dict[str, str] = {}

    redis = AsyncMock()
    redis.get = AsyncMock(side_effect=lambda key: store.get(key))
    redis.setex = AsyncMock(side_effect=lambda key, ttl, val: store.update({key: val}))
    redis.delete = AsyncMock(
        side_effect=lambda key: store.pop(key, None) is not None and 1 or 0
    )
    redis._store = store
    return redis


@pytest_asyncio.fixture
async def client(db: AsyncSession, mock_redis):
    """FastAPI test client with DB and Redis overrides."""

    async def override_db():
        yield db

    async def override_redis():
        yield mock_redis

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_redis] = override_redis

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def registered_user(db: AsyncSession) -> dict:
    """Create a user directly in DB and return credentials + token."""

    unique = request.node.name
    user = User(
        email=f"test-{unique}@example.com",
        username=f"testuser-{unique}",
        hashed_password=hash_password("Password123"),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    access_token = create_access_token(str(user.id))
    return {
        "user": user,
        "access_token": access_token,
        "headers": {"Authorization": f"Bearer {access_token}"},
    }


@pytest_asyncio.fixture
async def auth_client(client: AsyncClient, registered_user: dict) -> AsyncClient:
    """AsyncClient with auth headers pre-set."""
    client.headers.update(registered_user["headers"])
    return client
