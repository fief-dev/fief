import asyncio
import contextlib
import uuid
from typing import AsyncContextManager, AsyncGenerator, Callable

import asgi_lifespan
import httpx
import pytest
from fastapi.applications import FastAPI

from fief.app import app
from fief.db import (
    AsyncSession,
    create_async_session_maker,
    create_engine,
    get_global_async_session,
)
from fief.models import GlobalBase

global_engine = create_engine("sqlite+aiosqlite:///:memory:")
global_session_maker = create_async_session_maker(global_engine)


@pytest.fixture(scope="session")
def event_loop():
    """Force the pytest-asyncio loop to be the main one."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def create_global_db():
    async with global_engine.connect() as connection:
        await connection.run_sync(GlobalBase.metadata.create_all)


@pytest.fixture
async def test_async_session(create_global_db) -> AsyncGenerator[AsyncSession, None]:
    async with global_engine.connect() as connection:
        async with connection.begin() as transaction:
            async with global_session_maker() as session:
                yield session
            await transaction.rollback()


@pytest.fixture
def not_existing_uuid() -> uuid.UUID:
    return uuid.uuid4()


TestClientGeneratorType = Callable[[FastAPI], AsyncContextManager[httpx.AsyncClient]]


@pytest.fixture
async def test_client_generator(
    test_async_session: AsyncSession,
) -> TestClientGeneratorType:
    @contextlib.asynccontextmanager
    async def _test_client_generator(app: FastAPI):
        app.dependency_overrides = {}
        app.dependency_overrides[get_global_async_session] = lambda: test_async_session

        async with asgi_lifespan.LifespanManager(app):
            async with httpx.AsyncClient(
                app=app, base_url="http://api.fief.dev"
            ) as test_client:
                yield test_client

    return _test_client_generator


@pytest.fixture
async def test_client(
    test_client_generator: TestClientGeneratorType,
) -> AsyncGenerator[httpx.AsyncClient, None]:
    async with test_client_generator(app) as test_client:
        yield test_client
