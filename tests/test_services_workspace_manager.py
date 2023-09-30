import re
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from pytest_mock import MockerFixture
from sqlalchemy import select

from fief.db import AsyncSession
from fief.db.types import DatabaseConnectionParameters, DatabaseType
from fief.db.workspace import WorkspaceEngineManager, get_workspace_session
from fief.models import Client, User, Workspace
from fief.repositories import (
    ClientRepository,
    EmailTemplateRepository,
    TenantRepository,
    ThemeRepository,
    WorkspaceRepository,
    WorkspaceUserRepository,
)
from fief.schemas.workspace import WorkspaceCreate
from fief.services.email_template.types import EmailTemplateType
from fief.services.workspace_db import (
    WorkspaceDatabase,
    WorkspaceDatabaseConnectionError,
)
from fief.services.workspace_manager import WorkspaceManager
from tests.data import TestData
from tests.types import GetTestDatabase


@pytest_asyncio.fixture(scope="module")
async def test_database_url(
    get_test_database: GetTestDatabase,
) -> AsyncGenerator[tuple[DatabaseConnectionParameters, DatabaseType], None]:
    async with get_test_database(name="fief-test-workspace-manager") as (
        database_connection_parameters,
        database_type,
    ):
        yield database_connection_parameters, database_type


@pytest.fixture
def workspace_create(
    test_database_url: tuple[DatabaseConnectionParameters, DatabaseType]
) -> WorkspaceCreate:
    (url, _), database_type = test_database_url
    return WorkspaceCreate(
        name="Burgundy",
        database_type=database_type,
        database_use_schema=True,
        database_host=url.host,
        database_port=url.port,
        database_username=url.username,
        database_password=url.password,
        database_name=url.database,
        database_ssl_mode=None,
    )


@pytest.fixture
def workspace_engine_manager() -> WorkspaceEngineManager:
    return WorkspaceEngineManager()


@pytest.fixture
def workspace_manager(
    main_session: AsyncSession, workspace_engine_manager: WorkspaceEngineManager
) -> WorkspaceManager:
    workspace_repository = WorkspaceRepository(main_session)
    workspace_user_repository = WorkspaceUserRepository(main_session)
    workspace_db = WorkspaceDatabase()
    return WorkspaceManager(
        workspace_repository,
        workspace_user_repository,
        workspace_db,
        workspace_engine_manager,
        MagicMock(),
    )


@pytest.fixture
def main_fief_client(test_data: TestData) -> Client:
    return Client(
        name="Default",
        tenant=test_data["tenants"]["default"],
        client_id="DEFAULT_TENANT_CLIENT_ID",
        client_secret="DEFAULT_TENANT_CLIENT_SECRET",
        redirect_uris=["https://nantes.city/callback"],
    )


@pytest.fixture(autouse=True)
def mock_main_fief_functions(
    mocker: MockerFixture, workspace: Workspace, main_fief_client: Client
):
    get_main_fief_workspace_mock = mocker.patch(
        "fief.services.workspace_manager.get_main_fief_workspace"
    )
    get_main_fief_workspace_mock.side_effect = AsyncMock(return_value=workspace)

    get_main_fief_client_mock = mocker.patch(
        "fief.services.workspace_manager.get_main_fief_client"
    )
    get_main_fief_client_mock.side_effect = AsyncMock(return_value=main_fief_client)


@pytest.mark.asyncio
class TestWorkspaceManagerCreate:
    async def test_db_error(
        self,
        mocker: MockerFixture,
        workspace_create: WorkspaceCreate,
        workspace_manager: WorkspaceManager,
        main_session: AsyncSession,
    ):
        workspace_db_mock = mocker.patch.object(workspace_manager, "workspace_db")
        workspace_db_mock.migrate.side_effect = WorkspaceDatabaseConnectionError(
            "An error occured"
        )

        with pytest.raises(WorkspaceDatabaseConnectionError):
            await workspace_manager.create(workspace_create)

        workspace_repository = WorkspaceRepository(main_session)
        workspace = await workspace_repository.get_one_or_none(
            select(Workspace).where(Workspace.name == workspace_create.name)
        )
        assert workspace is None

    async def test_valid_db(
        self,
        workspace_create: WorkspaceCreate,
        workspace_manager: WorkspaceManager,
        workspace_engine_manager: WorkspaceEngineManager,
    ):
        workspace = await workspace_manager.create(workspace_create)

        assert workspace.domain == "burgundy.localhost:8000"
        assert workspace.alembic_revision is not None

        async with get_workspace_session(
            workspace, workspace_engine_manager
        ) as session:
            tenant_repository = TenantRepository(session)
            tenants = await tenant_repository.all()

            assert len(tenants) == 1
            tenant = tenants[0]
            assert tenant.default

            client_repository = ClientRepository(session)
            clients = await client_repository.all()

            assert len(clients) == 1
            client = clients[0]
            assert client.first_party
            assert client.tenant_id == tenant.id

            email_template_repository = EmailTemplateRepository(session)
            email_templates = await email_template_repository.all()

            assert len(email_templates) == len(EmailTemplateType)

            theme_repository = ThemeRepository(session)
            theme = await theme_repository.get_default()
            assert theme is not None

    async def test_user_id(
        self,
        workspace_create: WorkspaceCreate,
        workspace_manager: WorkspaceManager,
        workspace_admin_user: User,
        main_session: AsyncSession,
    ):
        workspace = await workspace_manager.create(
            workspace_create, workspace_admin_user.id
        )

        workspace_user_repository = WorkspaceUserRepository(main_session)
        workspace_user = await workspace_user_repository.get_by_workspace_and_user(
            workspace.id, workspace_admin_user.id
        )
        assert workspace_user is not None

    async def test_added_redirect_uri(
        self,
        workspace_create: WorkspaceCreate,
        workspace_manager: WorkspaceManager,
        workspace_admin_user: User,
        main_fief_client: Client,
    ):
        workspace = await workspace_manager.create(
            workspace_create, workspace_admin_user.id
        )

        assert (
            f"http://{workspace.domain}/admin/auth/callback"
            in main_fief_client.redirect_uris
        )

    async def test_default_parameters(
        self,
        workspace_create: WorkspaceCreate,
        workspace_manager: WorkspaceManager,
        workspace_engine_manager: WorkspaceEngineManager,
    ):
        workspace = await workspace_manager.create(
            workspace_create,
            default_domain="foobar.fief.dev",
            default_client_id="CLIENT_ID",
            default_client_secret="CLIENT_SECRET",
            default_encryption_key="ENCRYPTION_KEY",
        )

        assert workspace.domain == "foobar.fief.dev"

        async with get_workspace_session(
            workspace, workspace_engine_manager
        ) as session:
            client_repository = ClientRepository(session)
            clients = await client_repository.all()
            client = clients[0]

            assert client.encrypt_jwk == "ENCRYPTION_KEY"
            assert client.client_id == "CLIENT_ID"
            assert client.client_secret == "CLIENT_SECRET"

    async def test_avoid_domain_collision(
        self, workspace_create: WorkspaceCreate, workspace_manager: WorkspaceManager
    ):
        workspace_create.name = "Bretagne"
        workspace = await workspace_manager.create(workspace_create)

        assert re.match(r"bretagne-\w+\.localhost", workspace.domain)


@pytest.mark.asyncio
class TestWorkspaceManagerDelete:
    async def test_valid(
        self, workspace_create: WorkspaceCreate, workspace_manager: WorkspaceManager
    ):
        workspace = await workspace_manager.create(workspace_create)
        await workspace_manager.delete(workspace)
