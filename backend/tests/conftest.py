import asyncio
import contextlib
import dataclasses
import json
import os
import uuid
from typing import AsyncContextManager, AsyncGenerator, Callable, Optional
from unittest.mock import MagicMock

import asgi_lifespan
import httpx
import pytest
from fastapi import FastAPI
from fief_client import Fief

from fief.apps import admin_app, auth_app
from fief.crypto.access_token import generate_access_token
from fief.crypto.id_token import generate_id_token
from fief.db import (
    AsyncConnection,
    AsyncEngine,
    AsyncSession,
    create_engine,
    get_global_async_session,
)
from fief.dependencies.account import get_current_account_session
from fief.dependencies.account_creation import get_account_creation
from fief.dependencies.account_db import get_account_db
from fief.dependencies.fief import get_fief
from fief.managers.session_token import SessionTokenManager
from fief.models import (
    Account,
    AuthorizationCode,
    Client,
    GlobalBase,
    SessionToken,
    Tenant,
    User,
)
from fief.schemas.user import UserDB
from fief.services.account_creation import AccountCreation
from fief.services.account_db import AccountDatabase
from fief.settings import settings
from fief.utils.db_connection import get_database_url
from tests.data import TestData, data_mapping

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL", "postgresql://fief:fiefpassword@localhost:5432/fief-test"
)


@pytest.fixture(scope="session")
def event_loop():
    """Force the pytest-asyncio loop to be the main one."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def global_engine() -> AsyncGenerator[AsyncEngine, None]:
    engine = create_engine(get_database_url(TEST_DATABASE_URL))
    yield engine


@pytest.fixture(scope="session")
async def global_connection(
    global_engine: AsyncEngine,
) -> AsyncGenerator[AsyncConnection, None]:
    async with global_engine.connect() as connection:
        yield connection


@pytest.fixture(scope="session")
async def create_global_db(global_connection: AsyncConnection):
    await global_connection.run_sync(GlobalBase.metadata.create_all)


@pytest.fixture(scope="session")
async def global_session(
    global_connection: AsyncConnection, create_global_db
) -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSession(bind=global_connection, expire_on_commit=False) as session:
        await session.begin_nested()
        yield session
        await session.rollback()


@pytest.fixture(scope="session", autouse=True)
@pytest.mark.asyncio
async def account(global_session, create_global_db) -> AsyncGenerator[Account, None]:
    account = Account(
        name="Duché de Bretagne",
        domain="bretagne.fief.dev",
        database_url=get_database_url(TEST_DATABASE_URL, False),
    )
    global_session.add(account)
    await global_session.commit()

    account_db = AccountDatabase()
    account_db.migrate(account)

    yield account


@pytest.fixture(scope="session")
async def account_engine(account: Account) -> AsyncGenerator[AsyncEngine, None]:
    yield create_engine(account.get_database_url())


@pytest.fixture(scope="session")
async def account_connection(
    account_engine: AsyncEngine, account: Account
) -> AsyncGenerator[AsyncConnection, None]:
    async with account_engine.connect() as connection:
        connection = await connection.execution_options(
            schema_translate_map={None: str(account.id)}
        )
        await connection.begin()
        yield connection
        await connection.rollback()


@pytest.fixture(scope="session")
@pytest.mark.asyncio
async def test_data(account_connection: AsyncConnection) -> TestData:
    async with AsyncSession(bind=account_connection, expire_on_commit=False) as session:
        for model in data_mapping.values():
            for object in model.values():
                session.add(object)
        await session.commit()
    await account_connection.commit()
    yield data_mapping


@pytest.fixture()
async def account_session(
    account_connection: AsyncConnection,
) -> AsyncGenerator[AsyncSession, None]:
    await account_connection.begin_nested()
    async with AsyncSession(bind=account_connection, expire_on_commit=False) as session:
        yield session
    await account_connection.rollback()


@pytest.fixture
def not_existing_uuid() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
async def account_db_mock() -> MagicMock:
    return MagicMock(spec=AccountDatabase)


@pytest.fixture
async def account_creation_mock() -> MagicMock:
    return MagicMock(spec=AccountCreation)


@pytest.fixture
async def fief_client_mock() -> MagicMock:
    return MagicMock(spec=Fief)


@pytest.fixture
def account_host(request: pytest.FixtureRequest, account: Account) -> Optional[str]:
    marker = request.node.get_closest_marker("account_host")
    if marker:
        return account.domain
    return None


@pytest.fixture
async def session_token(
    request: pytest.FixtureRequest, test_data: TestData, global_session: AsyncSession
) -> Optional[str]:
    marker = request.node.get_closest_marker("session_token")
    if marker:
        user_alias = marker.kwargs["user"]
        user = test_data["users"][user_alias]

        userinfo = UserDB.from_orm(user).get_claims()
        session_token = SessionToken(raw_tokens="{}", raw_userinfo=json.dumps(userinfo))

        session_token_manager = SessionTokenManager(global_session)
        await session_token_manager.create(session_token)

        return session_token.token
    return None


@dataclasses.dataclass
class TenantParams:
    path_prefix: str
    tenant: Tenant
    client: Client
    user: User
    authorization_code: AuthorizationCode


@pytest.fixture(
    params=[
        {
            "path_prefix": "",
            "tenant_alias": "default",
            "client_alias": "default_tenant",
            "user_alias": "regular",
            "authorization_code_alias": "default_regular",
        },
        {
            "path_prefix": "/secondary",
            "tenant_alias": "secondary",
            "client_alias": "secondary_tenant",
            "user_alias": "regular_secondary",
            "authorization_code_alias": "secondary_regular",
        },
    ]
)
def tenant_params(request, test_data: TestData) -> TenantParams:
    params = request.param
    return TenantParams(
        path_prefix=params["path_prefix"],
        tenant=test_data["tenants"][params["tenant_alias"]],
        client=test_data["clients"][params["client_alias"]],
        user=test_data["users"][params["user_alias"]],
        authorization_code=test_data["authorization_codes"][
            params["authorization_code_alias"]
        ],
    )


@pytest.fixture
def access_token(
    request: pytest.FixtureRequest,
    test_data: TestData,
    tenant_params: TenantParams,
    account: Account,
) -> Optional[str]:
    marker = request.node.get_closest_marker("access_token")
    if marker:
        from_tenant_params: bool = marker.kwargs.get("from_tenant_params", False)
        if from_tenant_params:
            user = tenant_params.user
        else:
            user_alias = marker.kwargs["user"]
            user = test_data["users"][user_alias]

        user_tenant = user.tenant
        client = next(
            client
            for _, client in test_data["clients"].items()
            if client.tenant_id == user_tenant.id
        )

        return generate_access_token(
            user_tenant.get_sign_jwk(),
            user_tenant.get_host(account.domain),
            client,
            UserDB.from_orm(user),
            3600,
        )
    return None


TestClientGeneratorType = Callable[[FastAPI], AsyncContextManager[httpx.AsyncClient]]


@pytest.fixture
async def test_client_admin_generator(
    global_session: AsyncSession,
    account_session: AsyncSession,
    account_db_mock: MagicMock,
    account_creation_mock: MagicMock,
    fief_client_mock: MagicMock,
    account_host: Optional[str],
    session_token: Optional[str],
) -> TestClientGeneratorType:
    @contextlib.asynccontextmanager
    async def _test_client_generator(app: FastAPI):
        app.dependency_overrides = {}
        app.dependency_overrides[get_global_async_session] = lambda: global_session
        app.dependency_overrides[get_current_account_session] = lambda: account_session
        app.dependency_overrides[get_account_db] = lambda: account_db_mock
        app.dependency_overrides[get_account_creation] = lambda: account_creation_mock
        app.dependency_overrides[get_fief] = lambda: fief_client_mock

        headers = {}
        cookies = {}
        if account_host is not None:
            headers["Host"] = account_host
        if session_token is not None:
            cookies[settings.fief_admin_session_cookie_name] = session_token

        async with asgi_lifespan.LifespanManager(app):
            async with httpx.AsyncClient(
                app=app,
                base_url="http://api.fief.dev",
                headers=headers,
                cookies=cookies,
            ) as test_client:
                yield test_client

    return _test_client_generator


@pytest.fixture
async def test_client_admin(
    test_client_admin_generator: TestClientGeneratorType,
) -> AsyncGenerator[httpx.AsyncClient, None]:
    async with test_client_admin_generator(admin_app) as test_client:
        yield test_client


@pytest.fixture
async def test_client_auth_generator(
    global_session: AsyncSession,
    account_session: AsyncSession,
    account_db_mock: MagicMock,
    account_creation_mock: MagicMock,
    account_host: Optional[str],
    access_token: Optional[str],
) -> TestClientGeneratorType:
    @contextlib.asynccontextmanager
    async def _test_client_generator(app: FastAPI):
        app.dependency_overrides = {}
        app.dependency_overrides[get_global_async_session] = lambda: global_session
        app.dependency_overrides[get_current_account_session] = lambda: account_session
        app.dependency_overrides[get_account_db] = lambda: account_db_mock
        app.dependency_overrides[get_account_creation] = lambda: account_creation_mock

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
async def test_client_auth(
    test_client_auth_generator: TestClientGeneratorType,
) -> AsyncGenerator[httpx.AsyncClient, None]:
    async with test_client_auth_generator(auth_app) as test_client:
        yield test_client
