import asyncio
import contextlib
import os
import uuid
from typing import Any, AsyncContextManager, AsyncGenerator, Callable, Mapping

import asgi_lifespan
import httpx
import pytest
from fastapi.applications import FastAPI

from fief.app import app
from fief.db import (
    AsyncEngine,
    AsyncSession,
    create_async_session_maker,
    create_engine,
    get_global_async_session,
)
from fief.models import Account, GlobalBase
from fief.services.account_db import AccountDatabase
from tests.data import TestData, data_mapping


@pytest.fixture(scope="session")
def event_loop():
    """Force the pytest-asyncio loop to be the main one."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def global_engine() -> AsyncGenerator[AsyncEngine, None]:
    engine = create_engine("sqlite+aiosqlite:///global_test.db")
    yield engine
    os.remove("global_test.db")


@pytest.fixture(scope="session")
async def global_session_maker(global_engine: AsyncEngine):
    return create_async_session_maker(global_engine)


@pytest.fixture(scope="session")
async def create_global_db(global_engine: AsyncEngine):
    async with global_engine.connect() as connection:
        await connection.run_sync(GlobalBase.metadata.create_all)


@pytest.fixture(scope="session", autouse=True)
@pytest.mark.asyncio
async def account(
    global_engine: AsyncEngine, global_session_maker, create_global_db
) -> AsyncGenerator[Account, None]:
    async with global_session_maker() as session:
        account = Account(
            name="Duché de Bretagne", database_url="sqlite:///account_test.db"
        )
        session.add(account)
        await session.commit()

    account_db = AccountDatabase()
    account_db.migrate(account)

    yield account

    os.remove("account_test.db")


@pytest.fixture
async def global_session(
    global_engine: AsyncEngine, global_session_maker, create_global_db
) -> AsyncGenerator[AsyncSession, None]:
    async with global_engine.connect() as connection:
        async with connection.begin() as transaction:
            async with global_session_maker() as session:
                yield session
            await transaction.rollback()


@pytest.fixture(scope="session")
async def account_engine(account: Account) -> AsyncEngine:
    engine = create_engine(account.get_database_url())
    return engine


@pytest.fixture(scope="session")
async def account_session_maker(account_engine: AsyncEngine):
    return create_async_session_maker(account_engine)


@pytest.fixture
async def account_session(
    account_engine: AsyncEngine, account_session_maker
) -> AsyncGenerator[AsyncSession, None]:
    async with account_engine.connect() as connection:
        async with connection.begin() as transaction:
            async with account_session_maker() as session:
                yield session
            await transaction.rollback()


@pytest.fixture
def not_existing_uuid() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture(autouse=True)
@pytest.mark.asyncio
async def test_data(
    request: pytest.FixtureRequest, account_session: AsyncSession
) -> TestData:
    fixtures_marker = request.node.get_closest_marker("test_data")
    if fixtures_marker is None:
        return {}

    for model in data_mapping.values():
        for object in model.values():
            account_session.add(object)
    await account_session.commit()

    return data_mapping


TestClientGeneratorType = Callable[[FastAPI], AsyncContextManager[httpx.AsyncClient]]


@pytest.fixture
async def test_client_generator(
    global_session: AsyncSession,
) -> TestClientGeneratorType:
    @contextlib.asynccontextmanager
    async def _test_client_generator(app: FastAPI):
        app.dependency_overrides = {}
        app.dependency_overrides[get_global_async_session] = lambda: global_session

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
