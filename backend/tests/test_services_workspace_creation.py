import re
from typing import AsyncGenerator, Tuple
from unittest.mock import AsyncMock

import pytest
from pytest_mock import MockerFixture
from sqlalchemy import engine, select

from fief.db import AsyncSession
from fief.db.types import DatabaseType
from fief.db.workspace import get_workspace_session
from fief.managers import (
    ClientManager,
    TenantManager,
    WorkspaceManager,
    WorkspaceUserManager,
)
from fief.models import Client, Tenant, Workspace
from fief.schemas.user import UserDB
from fief.schemas.workspace import WorkspaceCreate
from fief.services.workspace_creation import WorkspaceCreation
from fief.services.workspace_db import WorkspaceDatabase
from tests.conftest import GetTestDatabase
from tests.data import TestData


@pytest.fixture(scope="module")
async def test_database_url(
    get_test_database: GetTestDatabase,
) -> AsyncGenerator[Tuple[engine.URL, DatabaseType], None]:
    async with get_test_database(name="fief-test-workspace-creation") as (
        url,
        database_type,
    ):
        yield url, database_type


@pytest.fixture
def workspace_create(
    test_database_url: Tuple[engine.URL, DatabaseType]
) -> WorkspaceCreate:
    url, database_type = test_database_url
    return WorkspaceCreate(
        name="Burgundy",
        database_type=database_type,
        database_host=url.host,
        database_port=url.port,
        database_username=url.username,
        database_password=url.password,
        database_name=url.database,
    )


@pytest.fixture
def workspace_creation(main_session: AsyncSession) -> WorkspaceCreation:
    workspace_manager = WorkspaceManager(main_session)
    workspace_user_manager = WorkspaceUserManager(main_session)
    workspace_db = WorkspaceDatabase()
    return WorkspaceCreation(workspace_manager, workspace_user_manager, workspace_db)


@pytest.fixture(autouse=True)
def mock_main_fief_functions(
    mocker: MockerFixture,
    workspace: Workspace,
    test_data: TestData,
    workspace_session: AsyncSession,
):
    get_main_fief_workspace_mock = mocker.patch(
        "fief.services.workspace_creation.get_main_fief_workspace"
    )
    get_main_fief_workspace_mock.side_effect = AsyncMock(return_value=workspace)

    get_main_fief_client_mock = mocker.patch(
        "fief.services.workspace_creation.get_main_fief_client"
    )
    get_main_fief_client_mock.side_effect = AsyncMock(
        return_value=test_data["clients"]["default_tenant"]
    )


@pytest.mark.asyncio
class TestWorkspaceCreationCreate:
    async def test_valid_db(
        self, workspace_create: WorkspaceCreate, workspace_creation: WorkspaceCreation
    ):
        workspace = await workspace_creation.create(workspace_create)

        assert workspace.domain == "burgundy.localhost"

        async with get_workspace_session(workspace) as session:
            tenant_manager = TenantManager(session)
            tenants = await tenant_manager.list(select(Tenant))

            assert len(tenants) == 1
            tenant = tenants[0]
            assert tenant.default

            client_manager = ClientManager(session)
            clients = await client_manager.list(select(Client))

            assert len(clients) == 1
            client = clients[0]
            assert client.first_party
            assert client.tenant_id == tenant.id

    async def test_user_id(
        self,
        workspace_create: WorkspaceCreate,
        workspace_creation: WorkspaceCreation,
        workspace_admin_user: UserDB,
        main_session: AsyncSession,
    ):
        workspace = await workspace_creation.create(
            workspace_create, workspace_admin_user.id
        )

        workspace_user_manager = WorkspaceUserManager(main_session)
        workspace_user = await workspace_user_manager.get_by_workspace_and_user(
            workspace.id, workspace_admin_user.id
        )
        assert workspace_user is not None

    async def test_added_redirect_uri(
        self,
        workspace_create: WorkspaceCreate,
        workspace_creation: WorkspaceCreation,
        workspace_admin_user: UserDB,
        workspace_session: AsyncSession,
        test_data: TestData,
    ):
        workspace = await workspace_creation.create(
            workspace_create, workspace_admin_user.id
        )

        client_manager = ClientManager(workspace_session)
        client = await client_manager.get_by_id(
            test_data["clients"]["default_tenant"].id
        )
        assert client is not None
        assert (
            f"http://{workspace.domain}/admin/api/auth/callback" in client.redirect_uris
        )

    async def test_default_parameters(
        self, workspace_create: WorkspaceCreate, workspace_creation: WorkspaceCreation
    ):
        workspace = await workspace_creation.create(
            workspace_create,
            default_domain="foobar.fief.dev",
            default_client_id="CLIENT_ID",
            default_client_secret="CLIENT_SECRET",
            default_encryption_key="ENCRYPTION_KEY",
        )

        assert workspace.domain == "foobar.fief.dev"

        async with get_workspace_session(workspace) as session:
            client_manager = ClientManager(session)
            clients = await client_manager.list(select(Client))
            client = clients[0]

            assert client.encrypt_jwk == "ENCRYPTION_KEY"
            assert client.client_id == "CLIENT_ID"
            assert client.client_secret == "CLIENT_SECRET"

    async def test_avoid_domain_collision(
        self, workspace_create: WorkspaceCreate, workspace_creation: WorkspaceCreation
    ):
        workspace_create.name = "Bretagne"
        workspace = await workspace_creation.create(workspace_create)

        assert re.match(r"bretagne-\w+\.localhost", workspace.domain)
