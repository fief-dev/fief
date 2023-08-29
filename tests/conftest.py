import asyncio
import contextlib
import json
import secrets
import uuid
from collections.abc import AsyncGenerator, Callable, Generator
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import asgi_lifespan
import httpx
import pytest
import pytest_asyncio
from dramatiq import Actor, Message
from fastapi import FastAPI
from sqlalchemy_utils import create_database, drop_database

from fief.apps import api_app, auth_app, dashboard_app
from fief.crypto.access_token import generate_access_token
from fief.crypto.token import generate_token
from fief.db import AsyncConnection, AsyncEngine, AsyncSession
from fief.db.engine import create_engine
from fief.db.types import DatabaseConnectionParameters, DatabaseType, get_driver
from fief.db.workspace import WorkspaceEngineManager, get_connection
from fief.dependencies.current_workspace import get_current_workspace_session
from fief.dependencies.db import get_main_async_session, get_workspace_engine_manager
from fief.dependencies.fief import FiefAsyncRelativeEndpoints, get_fief
from fief.dependencies.tasks import get_send_task
from fief.dependencies.tenant_email_domain import get_tenant_email_domain
from fief.dependencies.theme import get_theme_preview
from fief.dependencies.workspace_db import get_workspace_db
from fief.dependencies.workspace_manager import get_workspace_manager
from fief.models import (
    AdminAPIKey,
    AdminSessionToken,
    MainBase,
    User,
    Workspace,
    WorkspaceUser,
)
from fief.services.acr import ACR
from fief.services.tenant_email_domain import TenantEmailDomain
from fief.services.theme_preview import ThemePreview
from fief.services.workspace_db import WorkspaceDatabase
from fief.services.workspace_manager import WorkspaceManager
from fief.settings import settings
from tests.data import TestData, data_mapping, session_token_tokens
from tests.types import GetTestDatabase, HTTPClientGeneratorType, TenantParams

pytest.register_assert_rewrite("tests.helpers")


@pytest.fixture(scope="session")
def event_loop():
    """Force the pytest-asyncio loop to be the main one."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def get_test_database(worker_id: str) -> GetTestDatabase:
    @contextlib.asynccontextmanager
    async def _get_test_database(
        *, name: str = "fief-test", drop: bool = True
    ) -> AsyncGenerator[tuple[DatabaseConnectionParameters, DatabaseType], None]:
        url, connect_args = settings.get_database_connection_parameters(False)

        name = f"{name}-{worker_id}"
        url = url.set(database=name)
        assert url.database == name

        create_database(url)
        yield ((url, connect_args), settings.database_type)

        try:
            drop_database(url)
        # Silently ignore error when we try to drop an already removed SQLite DB
        except FileNotFoundError:
            pass

    return _get_test_database


@pytest_asyncio.fixture(scope="session")
async def main_test_database(
    get_test_database: GetTestDatabase,
) -> AsyncGenerator[tuple[DatabaseConnectionParameters, DatabaseType], None]:
    async with get_test_database() as (database_connection_parameters, database_type):
        url, connect_args = database_connection_parameters
        url = url.set(drivername=get_driver(database_type, asyncio=True))
        yield (url, connect_args), database_type


@pytest_asyncio.fixture(scope="session")
async def main_engine(
    main_test_database: tuple[DatabaseConnectionParameters, DatabaseType],
) -> AsyncGenerator[AsyncEngine, None]:
    database_connection_parameters, _ = main_test_database
    engine = create_engine(database_connection_parameters)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(scope="session")
async def main_connection(
    main_engine: AsyncEngine,
) -> AsyncGenerator[AsyncConnection, None]:
    async with main_engine.connect() as connection:
        yield connection


@pytest_asyncio.fixture(scope="session")
async def create_main_db(main_connection: AsyncConnection):
    await main_connection.run_sync(MainBase.metadata.create_all)


@pytest_asyncio.fixture(scope="session")
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


@pytest_asyncio.fixture(scope="session", autouse=True)
async def workspace(
    main_test_database: tuple[DatabaseConnectionParameters, DatabaseType],
    main_session,
    create_main_db,
) -> AsyncGenerator[Workspace, None]:
    (url, _), database_type = main_test_database
    workspace = Workspace(
        name="Duché de Bretagne",
        domain="bretagne.localhost:8000",
        database_type=database_type,
        database_host=url.host,
        database_port=url.port,
        database_username=url.username,
        database_password=url.password,
        database_name=url.database,
    )
    main_session.add(workspace)
    await main_session.commit()

    workspace_db = WorkspaceDatabase()
    revision = workspace_db.migrate(
        workspace.get_database_connection_parameters(False),
        workspace.database_table_prefix,
        workspace.schema_name,
    )
    workspace.alembic_revision = revision
    main_session.add(workspace)
    await main_session.commit()

    yield workspace


@pytest.fixture(scope="session")
def latest_revision(workspace: Workspace) -> str:
    assert workspace.alembic_revision is not None
    return workspace.alembic_revision


@pytest_asyncio.fixture(scope="session")
async def workspace_engine(workspace: Workspace) -> AsyncGenerator[AsyncEngine, None]:
    engine = create_engine(workspace.get_database_connection_parameters())
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(scope="session")
async def workspace_connection(
    workspace_engine: AsyncEngine, workspace: Workspace
) -> AsyncGenerator[AsyncConnection, None]:
    async with get_connection(
        workspace_engine,
        table_prefix=workspace.database_table_prefix,
        schema_name=workspace.schema_name,
    ) as connection:
        yield connection


@pytest_asyncio.fixture(scope="session")
async def test_data(
    workspace_connection: AsyncConnection,
) -> AsyncGenerator[TestData, None]:
    async with AsyncSession(
        bind=workspace_connection,
        expire_on_commit=False,
        join_transaction_mode="control_fully",
    ) as session:
        for model in data_mapping.values():
            for object in model.values():
                session.add(object)
        await session.commit()
    yield data_mapping


@pytest_asyncio.fixture
async def workspace_session(
    workspace_connection: AsyncConnection,
) -> AsyncGenerator[AsyncSession, None]:
    transaction = await workspace_connection.begin_nested()
    async with AsyncSession(
        bind=workspace_connection,
        expire_on_commit=False,
        join_transaction_mode="rollback_only",
    ) as session:
        yield session
    await transaction.rollback()


@pytest.fixture
def workspace_session_manager(workspace_session: AsyncSession):
    @contextlib.asynccontextmanager
    async def _workspace_session_manager(*args, **kwargs):
        yield workspace_session

    return _workspace_session_manager


@pytest.fixture
def not_existing_uuid() -> uuid.UUID:
    return uuid.uuid4()


@pytest_asyncio.fixture
async def workspace_db_mock(latest_revision: str) -> MagicMock:
    mock = MagicMock(spec=WorkspaceDatabase)
    mock.get_latest_revision.return_value = latest_revision
    return mock


@pytest_asyncio.fixture
async def workspace_manager_mock() -> MagicMock:
    return MagicMock(spec=WorkspaceManager)


@pytest_asyncio.fixture
async def fief_client_mock() -> MagicMock:
    return MagicMock(spec=FiefAsyncRelativeEndpoints)


@pytest_asyncio.fixture
async def tenant_email_domain_mock() -> MagicMock:
    return MagicMock(spec=TenantEmailDomain)


@pytest_asyncio.fixture
async def send_task_mock() -> MagicMock:
    def _send_task(task: Actor, *args, **kwargs):
        message: Message = Message(
            queue_name=task.queue_name,
            actor_name=task.actor_name,
            args=args,
            kwargs=kwargs or {},
            options={},
        )
        message.encode()

    return MagicMock(side_effect=_send_task)


@pytest_asyncio.fixture
async def theme_preview_mock() -> MagicMock:
    return MagicMock(spec=ThemePreview)


@pytest.fixture
def smtplib_mock() -> Generator[MagicMock, None, None]:
    with patch("smtplib.SMTP", autospec=True) as mock:
        yield mock


@pytest.fixture
def workspace_host(request: pytest.FixtureRequest, workspace: Workspace) -> str | None:
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


@contextlib.asynccontextmanager
async def create_admin_session_token(
    workspace: Workspace, user: User, main_session: AsyncSession
) -> AsyncGenerator[tuple[AdminSessionToken, str], None]:
    workspace_user = WorkspaceUser(workspace_id=workspace.id, user_id=user.id)
    main_session.add(workspace_user)

    token, token_hash = generate_token()
    session_token = AdminSessionToken(
        token=token_hash,
        raw_tokens="{}",
        raw_userinfo=json.dumps(user.get_claims()),
    )
    main_session.add(session_token)

    await main_session.commit()

    yield (session_token, token)

    await main_session.delete(workspace_user)


@contextlib.asynccontextmanager
async def create_api_key(
    workspace: Workspace, main_session: AsyncSession
) -> AsyncGenerator[tuple[AdminAPIKey, str], None]:
    token, token_hash = generate_token()
    admin_api_key = AdminAPIKey(
        name="API Key", token=token_hash, workspace_id=workspace.id
    )
    main_session.add(admin_api_key)
    await main_session.commit()

    yield (admin_api_key, token)

    await main_session.delete(admin_api_key)


@pytest_asyncio.fixture
async def admin_session_token(
    main_session: AsyncSession, workspace: Workspace, workspace_admin_user: User
) -> AsyncGenerator[tuple[AdminSessionToken, str], None]:
    async with create_admin_session_token(
        workspace, workspace_admin_user, main_session
    ) as result:
        yield result


@pytest_asyncio.fixture
async def admin_api_key(
    main_session: AsyncSession, workspace: Workspace
) -> AsyncGenerator[tuple[AdminAPIKey, str], None]:
    async with create_api_key(workspace, main_session) as result:
        yield result


@pytest_asyncio.fixture
async def alt_workspace(
    main_session: AsyncSession,
) -> AsyncGenerator[Workspace, None]:
    workspace = Workspace(name="Gascony", domain="gascony.localhost")
    main_session.add(workspace)
    await main_session.commit()

    yield workspace

    await main_session.delete(workspace)


@pytest_asyncio.fixture
async def admin_session_token_alt_workspace(
    main_session: AsyncSession, alt_workspace: Workspace
) -> AsyncGenerator[tuple[AdminSessionToken, str], None]:
    user_another_workspace = User(
        id=uuid.uuid4(),
        email="dev@gascony.duchy",
        hashed_password="dev",
        tenant_id=uuid.uuid4(),
    )
    async with create_admin_session_token(
        alt_workspace, user_another_workspace, main_session
    ) as result:
        yield result


@pytest_asyncio.fixture
async def admin_api_key_alt_workspace(
    main_session: AsyncSession, alt_workspace: Workspace
) -> AsyncGenerator[tuple[AdminAPIKey, str], None]:
    async with create_api_key(alt_workspace, main_session) as result:
        yield result


@pytest.fixture
def authenticated_admin(
    request: pytest.FixtureRequest,
    admin_session_token: tuple[AdminSessionToken, str],
    admin_api_key: tuple[AdminAPIKey, str],
    admin_session_token_alt_workspace: tuple[AdminSessionToken, str],
    admin_api_key_alt_workspace: tuple[AdminAPIKey, str],
) -> Callable[[httpx.AsyncClient], httpx.AsyncClient]:
    def _authenticated_admin(client: httpx.AsyncClient) -> httpx.AsyncClient:
        marker = request.node.get_closest_marker("authenticated_admin")
        if marker:
            mode = marker.kwargs.get("mode", "api_key")
            workspace = marker.kwargs.get("workspace", "main")
            assert mode in {"session", "api_key"}
            assert workspace in {"main", "alt"}
            if mode == "session":
                token = (
                    admin_session_token[1]
                    if workspace == "main"
                    else admin_session_token_alt_workspace[1]
                )
                client.cookies.set(settings.fief_admin_session_cookie_name, token)
            elif mode == "api_key":
                token = (
                    admin_api_key[1]
                    if workspace == "main"
                    else admin_api_key_alt_workspace[1]
                )
                client.headers["Authorization"] = f"Bearer {token}"
        return client

    return _authenticated_admin


@pytest.fixture(
    params=[
        {
            "path_prefix": "",
            "tenant_alias": "default",
            "client_alias": "default_tenant",
            "user_alias": "regular",
            "login_session_alias": "default",
            "registration_session_password_alias": "default_password",
            "registration_session_oauth_alias": "default_oauth",
            "session_token_alias": "regular",
        },
        {
            "path_prefix": "/secondary",
            "tenant_alias": "secondary",
            "client_alias": "secondary_tenant",
            "user_alias": "regular_secondary",
            "login_session_alias": "secondary",
            "registration_session_password_alias": "secondary_password",
            "registration_session_oauth_alias": "secondary_oauth",
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
        registration_session_password=test_data["registration_sessions"][
            params["registration_session_password_alias"]
        ],
        registration_session_oauth=test_data["registration_sessions"][
            params["registration_session_oauth_alias"]
        ],
        session_token=test_data["session_tokens"][params["session_token_alias"]],
        session_token_token=session_token_tokens[params["session_token_alias"]],
    )


@pytest.fixture
def access_token(
    request: pytest.FixtureRequest,
    test_data: TestData,
    tenant_params: TenantParams,
    workspace: Workspace,
) -> Callable[[httpx.AsyncClient], httpx.AsyncClient]:
    def _access_token(http_client: httpx.AsyncClient) -> httpx.AsyncClient:
        marker = request.node.get_closest_marker("access_token")
        if marker:
            from_tenant_params: bool = marker.kwargs.get("from_tenant_params", False)
            if from_tenant_params:
                user = tenant_params.user
            else:
                user_alias = marker.kwargs["user"]
                user = test_data["users"][user_alias]

            acr: ACR = marker.kwargs.get("acr", ACR.LEVEL_ZERO)

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

            access_token = generate_access_token(
                user_tenant.get_sign_jwk(),
                user_tenant.get_host(workspace.domain),
                client,
                datetime.now(UTC),
                acr,
                user,
                ["openid"],
                user_permissions,
                3600,
            )
            http_client.headers["Authorization"] = f"Bearer {access_token}"
        return http_client

    return _access_token


@pytest.fixture
def csrf_token() -> str:
    return secrets.token_urlsafe()


@pytest_asyncio.fixture
async def test_client_generator(
    main_session: AsyncSession,
    workspace_session: AsyncSession,
    workspace_db_mock: MagicMock,
    workspace_manager_mock: MagicMock,
    send_task_mock: MagicMock,
    fief_client_mock: MagicMock,
    theme_preview_mock: MagicMock,
    tenant_email_domain_mock: MagicMock,
    authenticated_admin: Callable[[httpx.AsyncClient], httpx.AsyncClient],
    access_token: Callable[[httpx.AsyncClient], httpx.AsyncClient],
    workspace_host: str | None,
) -> HTTPClientGeneratorType:
    @contextlib.asynccontextmanager
    async def _test_client_generator(app: FastAPI):
        app.dependency_overrides = {}
        app.dependency_overrides[get_main_async_session] = lambda: main_session
        app.dependency_overrides[
            get_current_workspace_session
        ] = lambda: workspace_session
        app.dependency_overrides[get_workspace_db] = lambda: workspace_db_mock
        app.dependency_overrides[
            get_workspace_engine_manager
        ] = lambda: WorkspaceEngineManager()
        app.dependency_overrides[get_workspace_manager] = lambda: workspace_manager_mock
        app.dependency_overrides[get_send_task] = lambda: send_task_mock
        app.dependency_overrides[get_fief] = lambda: fief_client_mock
        app.dependency_overrides[get_theme_preview] = lambda: theme_preview_mock
        app.dependency_overrides[
            get_tenant_email_domain
        ] = lambda: tenant_email_domain_mock
        settings.fief_admin_session_cookie_domain = ""

        async with asgi_lifespan.LifespanManager(app):
            async with httpx.AsyncClient(
                app=app, base_url="http://api.fief.dev"
            ) as test_client:
                test_client = authenticated_admin(test_client)
                test_client = access_token(test_client)
                if workspace_host is not None:
                    test_client.headers["Host"] = workspace_host
                yield test_client

    return _test_client_generator


@pytest_asyncio.fixture
async def test_client_api(
    test_client_generator: HTTPClientGeneratorType,
) -> AsyncGenerator[httpx.AsyncClient, None]:
    async with test_client_generator(api_app) as test_client:
        yield test_client


@pytest.fixture(params=[False, True], ids=["Without HTMX", "With HTMX"])
def htmx(request: pytest.FixtureRequest):
    def _htmx(client: httpx.AsyncClient) -> httpx.AsyncClient:
        if request.param:
            client.headers["HX-Request"] = "true"
            marker = request.node.get_closest_marker("htmx")
            if marker:
                target: str | None = marker.kwargs.get("target")
                if target:
                    client.headers["HX-Target"] = target
        return client

    return _htmx


@pytest_asyncio.fixture
async def test_client_dashboard(
    test_client_generator: HTTPClientGeneratorType,
    htmx: Callable[[httpx.AsyncClient], httpx.AsyncClient],
    csrf_token: str,
) -> AsyncGenerator[httpx.AsyncClient, None]:
    async with test_client_generator(dashboard_app) as test_client:
        test_client.cookies.set(settings.csrf_cookie_name, csrf_token)
        test_client = htmx(test_client)
        yield test_client


@pytest_asyncio.fixture
async def test_client_auth(
    test_client_generator: HTTPClientGeneratorType,
) -> AsyncGenerator[httpx.AsyncClient, None]:
    async with test_client_generator(auth_app) as test_client:
        yield test_client


@pytest_asyncio.fixture
async def test_client_auth_csrf(
    test_client_auth: httpx.AsyncClient, csrf_token: str
) -> AsyncGenerator[httpx.AsyncClient, None]:
    test_client_auth.cookies.set(settings.csrf_cookie_name, csrf_token)
    yield test_client_auth


def pytest_generate_tests(metafunc: pytest.Metafunc):
    """
    Automatically parametrize tests which include
    `unauthorized_dashboard_assertions` or `unauthorized_api_assertions` fixture.

    The parametrization adds two cases:

    * A case where the client is not authenticated.
    * A case where the client is authenticated on another workspace.

    The parametrization injects the corresponding assertion function for each case.

    It helps to quickly add tests for those cases that are critical for security.
    """
    if "unauthorized_dashboard_assertions" in metafunc.fixturenames:
        from tests.helpers import (
            dashboard_unauthorized_alt_workspace_assertions,
            dashboard_unauthorized_assertions,
        )

        metafunc.parametrize(
            "unauthorized_dashboard_assertions",
            [
                pytest.param(dashboard_unauthorized_assertions, id="Unauthorized"),
                pytest.param(
                    dashboard_unauthorized_alt_workspace_assertions,
                    marks=pytest.mark.authenticated_admin(
                        mode="session", workspace="alt"
                    ),
                    id="Alt workspace",
                ),
            ],
        )
    elif "unauthorized_api_assertions" in metafunc.fixturenames:
        from tests.helpers import (
            api_unauthorized_alt_workspace_assertions,
            api_unauthorized_assertions,
        )

        metafunc.parametrize(
            "unauthorized_api_assertions",
            [
                pytest.param(api_unauthorized_assertions, id="Unauthorized"),
                pytest.param(
                    api_unauthorized_alt_workspace_assertions,
                    marks=pytest.mark.authenticated_admin(
                        mode="api_key", workspace="alt"
                    ),
                    id="Alt workspace",
                ),
            ],
        )
