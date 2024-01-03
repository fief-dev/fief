import asyncio
import contextlib
import json
import secrets
import uuid
from collections.abc import AsyncGenerator, Callable, Generator
from typing import cast
from unittest.mock import MagicMock, patch

import asgi_lifespan
import httpx
import pytest
import pytest_asyncio
from alembic import command
from alembic.config import Config
from dramatiq import Actor, Message
from fastapi import FastAPI
from fief_client import FiefAsync
from sqlalchemy_utils import create_database, drop_database

from fief.apps import api_app, auth_app, dashboard_app
from fief.crypto.token import generate_token
from fief.db import AsyncEngine, AsyncSession
from fief.db.engine import create_engine
from fief.db.types import DatabaseConnectionParameters, DatabaseType, get_driver
from fief.dependencies.db import get_main_async_session
from fief.dependencies.fief import get_fief
from fief.dependencies.tasks import get_send_task
from fief.dependencies.tenant_email_domain import get_tenant_email_domain
from fief.dependencies.theme import get_theme_preview
from fief.models import AdminAPIKey, AdminSessionToken, User
from fief.paths import ALEMBIC_CONFIG_FILE
from fief.services.tenant_email_domain import TenantEmailDomain
from fief.services.theme_preview import ThemePreview
from fief.settings import settings
from tests.data import ModelMapping, TestData, data_mapping, session_token_tokens
from tests.types import GetTestDatabase, HTTPClientGeneratorType, TenantParams

pytest.register_assert_rewrite("tests.helpers")


@pytest.fixture(scope="session")
def event_loop():
    """Force the pytest-asyncio loop to be the main one."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
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


@pytest_asyncio.fixture(scope="session", autouse=True)
async def main_test_database(
    get_test_database: GetTestDatabase,
) -> AsyncGenerator[tuple[DatabaseConnectionParameters, DatabaseType], None]:
    async with get_test_database() as (database_connection_parameters, database_type):
        url, connect_args = database_connection_parameters
        url = url.set(drivername=get_driver(database_type, asyncio=True))
        yield (url, connect_args), database_type


@pytest_asyncio.fixture(scope="session", autouse=True)
async def main_engine(
    main_test_database: tuple[DatabaseConnectionParameters, DatabaseType],
) -> AsyncGenerator[AsyncEngine, None]:
    database_connection_parameters, _ = main_test_database
    engine = create_engine(database_connection_parameters)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def create_main_db(main_engine: AsyncEngine):
    async with main_engine.begin() as connection:

        def _run_upgrade(connection):
            alembic_config = Config(ALEMBIC_CONFIG_FILE, ini_section="main")
            alembic_config.attributes["connection"] = connection
            alembic_config.attributes["table_prefix"] = settings.database_table_prefix
            command.upgrade(alembic_config, "head")

        await connection.run_sync(_run_upgrade)


@pytest_asyncio.fixture(scope="session")
async def test_data(
    main_engine: AsyncEngine, create_main_db
) -> AsyncGenerator[TestData, None]:
    async with main_engine.begin() as connection:
        async with AsyncSession(bind=connection, expire_on_commit=False) as session:
            for model in data_mapping.values():
                for object in cast(ModelMapping, model).values():
                    session.add(object)
            await session.commit()
    yield data_mapping


@pytest_asyncio.fixture
async def main_session(main_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    connection = await main_engine.connect()
    transaction = await connection.begin()

    session = AsyncSession(
        bind=connection,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    yield session

    session.expunge_all()
    await transaction.rollback()
    await connection.close()


@pytest.fixture
def main_session_manager(main_session: AsyncSession):
    @contextlib.asynccontextmanager
    async def _main_session_manager(*args, **kwargs):
        yield main_session

    return _main_session_manager


@pytest.fixture
def not_existing_uuid() -> uuid.UUID:
    return uuid.uuid4()


@pytest_asyncio.fixture
async def fief_client_mock() -> MagicMock:
    return MagicMock(spec=FiefAsync)


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


@contextlib.asynccontextmanager
async def create_admin_session_token(
    user: User, main_session: AsyncSession
) -> AsyncGenerator[tuple[AdminSessionToken, str], None]:
    token, token_hash = generate_token()
    session_token = AdminSessionToken(
        token=token_hash,
        raw_tokens="{}",
        raw_userinfo=json.dumps(user.get_claims()),
    )
    main_session.add(session_token)

    await main_session.commit()

    yield (session_token, token)


@contextlib.asynccontextmanager
async def create_api_key(
    main_session: AsyncSession,
) -> AsyncGenerator[tuple[AdminAPIKey, str], None]:
    token, token_hash = generate_token()
    admin_api_key = AdminAPIKey(name="API Key", token=token_hash)
    main_session.add(admin_api_key)
    await main_session.commit()

    yield (admin_api_key, token)

    await main_session.delete(admin_api_key)


@pytest_asyncio.fixture
async def admin_session_token(
    main_session: AsyncSession, test_data: TestData
) -> AsyncGenerator[tuple[AdminSessionToken, str], None]:
    user = test_data["users"]["regular"]
    async with create_admin_session_token(user, main_session) as result:
        yield result


@pytest_asyncio.fixture
async def admin_api_key(
    main_session: AsyncSession,
) -> AsyncGenerator[tuple[AdminAPIKey, str], None]:
    async with create_api_key(main_session) as result:
        yield result


@pytest.fixture
def authenticated_admin(
    request: pytest.FixtureRequest,
    admin_session_token: tuple[AdminSessionToken, str],
    admin_api_key: tuple[AdminAPIKey, str],
) -> Callable[[httpx.AsyncClient], httpx.AsyncClient]:
    def _authenticated_admin(client: httpx.AsyncClient) -> httpx.AsyncClient:
        marker = request.node.get_closest_marker("authenticated_admin")
        if marker:
            mode = marker.kwargs.get("mode", "api_key")
            assert mode in {"session", "api_key"}
            if mode == "session":
                _, token = admin_session_token
                client.cookies.set(settings.fief_admin_session_cookie_name, token)
            elif mode == "api_key":
                _, token = admin_api_key
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
def csrf_token() -> str:
    return secrets.token_urlsafe()


@pytest_asyncio.fixture
async def test_client_generator(
    main_session: AsyncSession,
    send_task_mock: MagicMock,
    fief_client_mock: MagicMock,
    theme_preview_mock: MagicMock,
    tenant_email_domain_mock: MagicMock,
    authenticated_admin: Callable[[httpx.AsyncClient], httpx.AsyncClient],
) -> HTTPClientGeneratorType:
    @contextlib.asynccontextmanager
    async def _test_client_generator(app: FastAPI):
        app.dependency_overrides = {}
        app.dependency_overrides[get_main_async_session] = lambda: main_session
        app.dependency_overrides[get_send_task] = lambda: send_task_mock
        app.dependency_overrides[get_fief] = lambda: fief_client_mock
        app.dependency_overrides[get_theme_preview] = lambda: theme_preview_mock
        app.dependency_overrides[get_tenant_email_domain] = (
            lambda: tenant_email_domain_mock
        )
        settings.fief_admin_session_cookie_domain = ""

        async with asgi_lifespan.LifespanManager(app):
            async with httpx.AsyncClient(
                app=app, base_url="http://api.fief.dev"
            ) as test_client:
                test_client = authenticated_admin(test_client)
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
        from tests.helpers import dashboard_unauthorized_assertions

        metafunc.parametrize(
            "unauthorized_dashboard_assertions",
            [
                pytest.param(dashboard_unauthorized_assertions, id="Unauthorized"),
            ],
        )
    elif "unauthorized_api_assertions" in metafunc.fixturenames:
        from tests.helpers import api_unauthorized_assertions

        metafunc.parametrize(
            "unauthorized_api_assertions",
            [pytest.param(api_unauthorized_assertions, id="Unauthorized")],
        )
