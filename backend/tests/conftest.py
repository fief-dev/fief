import asyncio
import contextlib
import os
import uuid
from typing import AsyncContextManager, AsyncGenerator, Callable, Optional
from unittest.mock import MagicMock

import asgi_lifespan
import httpx
import pytest
from fastapi import FastAPI

from fief.apps import admin_app, user_app
from fief.crypto.access_token import generate_access_token
from fief.db import (
    AsyncEngine,
    AsyncSession,
    create_async_session_maker,
    create_engine,
    get_global_async_session,
)
from fief.dependencies.account import get_current_account_session
from fief.dependencies.account_db import get_account_db
from fief.models import Account, GlobalBase
from fief.schemas.user import UserDB
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
    global_session_maker, create_global_db
) -> AsyncGenerator[Account, None]:
    async with global_session_maker() as session:
        account = Account(
            name="Duché de Bretagne",
            domain="bretagne.fief.dev",
            database_url="sqlite:///account_test.db",
        )
        session.add(account)
        await session.commit()

    account_db = AccountDatabase()
    account_db.migrate(account)

    yield account

    os.remove("account_test.db")


@pytest.fixture
async def global_session(
    global_engine: AsyncEngine, create_global_db
) -> AsyncGenerator[AsyncSession, None]:
    async with global_engine.connect() as connection:
        async with AsyncSession(bind=connection, expire_on_commit=False) as session:
            await session.begin_nested()
            yield session
            await session.rollback()


@pytest.fixture(scope="session")
async def account_engine(account: Account) -> AsyncEngine:
    engine = create_engine(account.get_database_url())
    return engine


@pytest.fixture
async def account_session(
    account_engine: AsyncEngine,
) -> AsyncGenerator[AsyncSession, None]:
    async with account_engine.connect() as connection:
        async with AsyncSession(bind=connection, expire_on_commit=False) as session:
            await session.begin_nested()
            yield session
            print("ROLLBACK")
            await session.rollback()


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
    account_session.expunge_all()

    return data_mapping


@pytest.fixture
async def account_db_mock() -> MagicMock:
    return MagicMock(spec=AccountDatabase)


@pytest.fixture
def account_host(request: pytest.FixtureRequest, account: Account) -> Optional[str]:
    marker = request.node.get_closest_marker("account_host")
    if marker:
        return account.domain
    return None


@pytest.fixture
def access_token(
    request: pytest.FixtureRequest, test_data: TestData, account: Account
) -> Optional[str]:
    marker = request.node.get_closest_marker("access_token")
    if marker:
        user_alias = marker.kwargs["user"]
        user = test_data["users"][user_alias]
        client = test_data["clients"]["default_tenant"]
        return generate_access_token(
            account.get_sign_jwk(), account, client, UserDB.from_orm(user), 3600
        )
    return None


TestClientGeneratorType = Callable[[FastAPI], AsyncContextManager[httpx.AsyncClient]]


@pytest.fixture
async def test_client_generator(
    global_session: AsyncSession,
    account_session: AsyncSession,
    account_db_mock: MagicMock,
    account_host: Optional[str],
    access_token: Optional[str],
) -> TestClientGeneratorType:
    @contextlib.asynccontextmanager
    async def _test_client_generator(app: FastAPI):
        app.dependency_overrides = {}
        app.dependency_overrides[get_global_async_session] = lambda: global_session
        app.dependency_overrides[get_current_account_session] = lambda: account_session
        app.dependency_overrides[get_account_db] = lambda: account_db_mock

        headers = {}
        if account_host is not None:
            headers["Host"] = account_host
        if access_token is not None:
            headers["Authorization"] = f"Bearer {access_token}"

        async with asgi_lifespan.LifespanManager(app):
            async with httpx.AsyncClient(
                app=app, base_url="http://api.fief.dev", headers=headers
            ) as test_client:
                yield test_client

    return _test_client_generator


@pytest.fixture
async def test_client_admin(
    test_client_generator: TestClientGeneratorType,
) -> AsyncGenerator[httpx.AsyncClient, None]:
    async with test_client_generator(admin_app) as test_client:
        yield test_client


@pytest.fixture
async def test_client_user(
    test_client_generator: TestClientGeneratorType,
) -> AsyncGenerator[httpx.AsyncClient, None]:
    async with test_client_generator(user_app) as test_client:
        yield test_client
