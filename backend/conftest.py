import asyncio
import contextlib
import json
import uuid
from typing import Any, AsyncGenerator, Dict, Optional, Tuple
from unittest.mock import MagicMock

import asgi_lifespan
import httpx
import pytest
from fastapi import FastAPI
from sqlalchemy import engine
from sqlalchemy_utils import create_database, drop_database

from fief.apps import admin_app, auth_app
from fief.crypto.access_token import generate_access_token
from fief.crypto.token import generate_token
from fief.csrf import check_csrf
from fief.db import AsyncConnection, AsyncEngine, AsyncSession
from fief.db.engine import create_engine
from fief.db.main import get_main_async_session
from fief.db.types import DatabaseType, get_driver
from fief.db.workspace import get_connection
from fief.dependencies.current_workspace import get_current_workspace_session
from fief.dependencies.fief import FiefAsyncRelativeEndpoints, get_fief
from fief.dependencies.tasks import get_send_task
from fief.dependencies.workspace_creation import get_workspace_creation
from fief.dependencies.workspace_db import get_workspace_db
from fief.models import (
    AdminAPIKey,
    AdminSessionToken,
    MainBase,
    User,
    Workspace,
    WorkspaceUser,
)
from fief.services.workspace_creation import WorkspaceCreation
from fief.services.workspace_db import WorkspaceDatabase
from fief.settings import settings
from fief.tasks import send_task
from tests.data import TestData, data_mapping, session_token_tokens
from tests.types import GetTestDatabase, TenantParams, TestClientGeneratorType

pytest.register_assert_rewrite("tests.helpers")


@pytest.fixture(scope="session")
def event_loop():
    """Force the pytest-asyncio loop to be the main one."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def get_test_database() -> GetTestDatabase:
    @contextlib.asynccontextmanager
    async def _get_test_database(
        *, name: str = "fief-test"
    ) -> AsyncGenerator[Tuple[engine.URL, DatabaseType], None]:
        url = settings.get_database_url(False).set(database=name)
        assert url.database == name
        create_database(url)
        yield (url, settings.database_type)
        drop_database(url)

    return _get_test_database


@pytest.fixture(scope="session")
async def main_test_database(
    get_test_database: GetTestDatabase,
) -> AsyncGenerator[Tuple[engine.URL, DatabaseType], None]:
    async with get_test_database() as (url, database_type):
        url = url.set(drivername=get_driver(database_type, asyncio=True))
        yield url, database_type


@pytest.fixture(scope="session")
async def main_engine(
    main_test_database: Tuple[engine.URL, DatabaseType],
) -> AsyncGenerator[AsyncEngine, None]:
    url, _ = main_test_database
    engine = create_engine(url)
    yield engine
    await engine.dispose()


@pytest.fixture(scope="session")
async def main_connection(
    main_engine: AsyncEngine,
) -> AsyncGenerator[AsyncConnection, None]:
    async with main_engine.connect() as connection:
        yield connection


@pytest.fixture(scope="session")
async def create_main_db(main_connection: AsyncConnection):
    await main_connection.run_sync(MainBase.metadata.create_all)


@pytest.fixture(scope="session")
async def main_session(
    main_connection: AsyncConnection, create_main_db
) -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSession(bind=main_connection, expire_on_commit=False) as session:
        await session.begin_nested()
        yield session
        await session.rollback()


@pytest.fixture(scope="session")
def main_session_manager(main_session: AsyncSession):
    @contextlib.asynccontextmanager
    async def _main_session_manager(*args, **kwargs):
        yield main_session

    return _main_session_manager


@pytest.fixture(scope="session", autouse=True)
@pytest.mark.asyncio
async def workspace(
    main_test_database: Tuple[engine.URL, DatabaseType],
    main_session,
    create_main_db,
) -> AsyncGenerator[Workspace, None]:
    url, database_type = main_test_database
    workspace = Workspace(
        name="Duché de Bretagne",
        domain="bretagne.localhost:8000",
        database_type=database_type,
        database_host=url.host,
        database_port=url.port,
        database_username=url.username,
        database_password=url.password,
        database_name=url.database,
        alembic_revision="LATEST",
    )
    main_session.add(workspace)
    await main_session.commit()

    workspace_db = WorkspaceDatabase()
    workspace_db.migrate(workspace.get_database_url(False), workspace.get_schema_name())

    yield workspace


@pytest.fixture(scope="session")
async def workspace_engine(workspace: Workspace) -> AsyncGenerator[AsyncEngine, None]:
    engine = create_engine(workspace.get_database_url())
    yield engine
    await engine.dispose()


@pytest.fixture(scope="session")
async def workspace_connection(
    workspace_engine: AsyncEngine, workspace: Workspace
) -> AsyncGenerator[AsyncConnection, None]:
    async with get_connection(
        workspace_engine, workspace.get_schema_name()
    ) as connection:
        await connection.begin()
        yield connection
        await connection.rollback()


@pytest.fixture(scope="session")
@pytest.mark.asyncio
async def test_data(workspace_connection: AsyncConnection) -> TestData:
    async with AsyncSession(
        bind=workspace_connection, expire_on_commit=False
    ) as session:
        for model in data_mapping.values():
            for object in model.values():
                session.add(object)
        await session.commit()
    await workspace_connection.commit()
    yield data_mapping


@pytest.fixture
async def workspace_session(
    workspace_connection: AsyncConnection,
) -> AsyncGenerator[AsyncSession, None]:
    await workspace_connection.begin_nested()
    async with AsyncSession(
        bind=workspace_connection, expire_on_commit=False
    ) as session:
        yield session
    await workspace_connection.rollback()


@pytest.fixture
def workspace_session_manager(workspace_session: AsyncSession):
    @contextlib.asynccontextmanager
    async def _workspace_session_manager(*args, **kwargs):
        yield workspace_session

    return _workspace_session_manager


@pytest.fixture
def not_existing_uuid() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
async def workspace_db_mock() -> MagicMock:
    mock = MagicMock(spec=WorkspaceDatabase)
    mock.get_latest_revision.return_value = "LATEST"
    return mock


@pytest.fixture
async def workspace_creation_mock() -> MagicMock:
    return MagicMock(spec=WorkspaceCreation)


@pytest.fixture
async def fief_client_mock() -> MagicMock:
    return MagicMock(spec=FiefAsyncRelativeEndpoints)


@pytest.fixture
async def send_task_mock() -> MagicMock:
    return MagicMock(spec=send_task)


@pytest.fixture
def workspace_host(
    request: pytest.FixtureRequest, workspace: Workspace
) -> Optional[str]:
    marker = request.node.get_closest_marker("workspace_host")
    if marker:
        return workspace.domain
    return None


@pytest.fixture
def workspace_admin_user() -> User:
    return User(
        id=uuid.uuid4(),
        email="dev@bretagne.duchy",
        hashed_password="dev",
        tenant_id=uuid.uuid4(),
    )


@pytest.fixture
async def admin_session_token(
    main_session: AsyncSession,
    workspace: Workspace,
    workspace_admin_user: User,
) -> AsyncGenerator[Tuple[AdminSessionToken, str], None]:
    workspace_user = WorkspaceUser(
        workspace_id=workspace.id, user_id=workspace_admin_user.id
    )
    main_session.add(workspace_user)
    await main_session.commit()

    token, token_hash = generate_token()
    session_token = AdminSessionToken(
        token=token_hash,
        raw_tokens="{}",
        raw_userinfo=json.dumps(workspace_admin_user.get_claims()),
    )
    main_session.add(session_token)

    await main_session.commit()

    yield (session_token, token)

    await main_session.delete(session_token)
    await main_session.delete(workspace_user)


@pytest.fixture
async def admin_api_key(
    main_session: AsyncSession, workspace: Workspace
) -> AsyncGenerator[Tuple[AdminAPIKey, str], None]:
    token, token_hash = generate_token()
    admin_api_key = AdminAPIKey(
        name="API Key", token=token_hash, workspace_id=workspace.id
    )
    main_session.add(admin_api_key)
    await main_session.commit()

    yield (admin_api_key, token)

    await main_session.delete(admin_api_key)


@pytest.fixture
async def authenticated_admin(
    request: pytest.FixtureRequest,
    admin_session_token: Tuple[AdminSessionToken, str],
    admin_api_key: Tuple[AdminAPIKey, str],
) -> Dict[str, Any]:
    marker = request.node.get_closest_marker("authenticated_admin")
    headers = {}
    if marker:
        mode = marker.kwargs.get("mode", "api_key")
        if mode == "session":
            headers[
                "Cookie"
            ] = f"{settings.fief_admin_session_cookie_name}={admin_session_token[1]}"
        elif mode == "api_key":
            headers["Authorization"] = f"Bearer {admin_api_key[1]}"
    return headers


@pytest.fixture(
    params=[
        {
            "path_prefix": "",
            "tenant_alias": "default",
            "client_alias": "default_tenant",
            "user_alias": "regular",
            "login_session_alias": "default",
            "session_token_alias": "regular",
        },
        {
            "path_prefix": "/secondary",
            "tenant_alias": "secondary",
            "client_alias": "secondary_tenant",
            "user_alias": "regular_secondary",
            "login_session_alias": "secondary",
            "session_token_alias": "regular_secondary",
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
        login_session=test_data["login_sessions"][params["login_session_alias"]],
        session_token=test_data["session_tokens"][params["session_token_alias"]],
        session_token_token=session_token_tokens[params["session_token_alias"]],
    )


@pytest.fixture
def access_token(
    request: pytest.FixtureRequest,
    test_data: TestData,
    tenant_params: TenantParams,
    workspace: Workspace,
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

        user_permissions = [
            permission.permission.codename
            for permission in test_data["user_permissions"].values()
        ]

        return generate_access_token(
            user_tenant.get_sign_jwk(),
            user_tenant.get_host(workspace.domain),
            client,
            user,
            ["openid"],
            user_permissions,
            3600,
        )
    return None


@pytest.fixture
async def test_client_admin_generator(
    main_session: AsyncSession,
    workspace_session: AsyncSession,
    workspace_db_mock: MagicMock,
    workspace_creation_mock: MagicMock,
    send_task_mock: MagicMock,
    fief_client_mock: MagicMock,
    authenticated_admin: Dict[str, Any],
    workspace_host: Optional[str],
) -> TestClientGeneratorType:
    @contextlib.asynccontextmanager
    async def _test_client_generator(app: FastAPI):
        app.dependency_overrides = {}
        app.dependency_overrides[get_main_async_session] = lambda: main_session
        app.dependency_overrides[
            get_current_workspace_session
        ] = lambda: workspace_session
        app.dependency_overrides[get_workspace_db] = lambda: workspace_db_mock
        app.dependency_overrides[
            get_workspace_creation
        ] = lambda: workspace_creation_mock
        app.dependency_overrides[get_send_task] = lambda: send_task_mock
        app.dependency_overrides[get_fief] = lambda: fief_client_mock
        settings.fief_admin_session_cookie_domain = ""

        headers = {**authenticated_admin}
        if workspace_host is not None:
            headers["Host"] = workspace_host

        async with asgi_lifespan.LifespanManager(app):
            async with httpx.AsyncClient(
                app=app,
                base_url="http://api.fief.dev",
                headers=headers,
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
    main_session: AsyncSession,
    workspace_session: AsyncSession,
    workspace_db_mock: MagicMock,
    workspace_creation_mock: MagicMock,
    send_task_mock: MagicMock,
    workspace_host: Optional[str],
    access_token: Optional[str],
) -> TestClientGeneratorType:
    @contextlib.asynccontextmanager
    async def _test_client_generator(app: FastAPI):
        app.dependency_overrides = {}
        app.dependency_overrides[get_main_async_session] = lambda: main_session
        app.dependency_overrides[
            get_current_workspace_session
        ] = lambda: workspace_session
        app.dependency_overrides[get_workspace_db] = lambda: workspace_db_mock
        app.dependency_overrides[
            get_workspace_creation
        ] = lambda: workspace_creation_mock
        app.dependency_overrides[check_csrf] = lambda: None
        app.dependency_overrides[get_send_task] = lambda: send_task_mock

        headers = {}
        if workspace_host is not None:
            headers["Host"] = workspace_host
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
