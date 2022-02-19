import re
from typing import AsyncGenerator, Tuple

import pytest
from sqlalchemy import engine, select

from fief.db import AsyncSession, get_account_session
from fief.db.types import DatabaseType
from fief.managers import (
    AccountManager,
    AccountUserManager,
    ClientManager,
    TenantManager,
)
from fief.models import Client, Tenant
from fief.schemas.account import AccountCreate
from fief.schemas.user import UserDB
from fief.services.account_creation import AccountCreation
from fief.services.account_db import AccountDatabase
from tests.conftest import GetTestDatabase


@pytest.fixture(scope="module")
async def test_database_url(
    get_test_database: GetTestDatabase,
) -> AsyncGenerator[Tuple[engine.URL, DatabaseType], None]:
    async with get_test_database(name="fief-test-account-creation") as (
        url,
        database_type,
    ):
        yield url, database_type


@pytest.fixture
def account_create(test_database_url: Tuple[engine.URL, DatabaseType]) -> AccountCreate:
    url, database_type = test_database_url
    return AccountCreate(
        name="Burgundy",
        database_type=database_type,
        database_host=url.host,
        database_port=url.port,
        database_username=url.username,
        database_password=url.password,
        database_name=url.database,
    )


@pytest.fixture
def account_creation(global_session: AsyncSession) -> AccountCreation:
    account_manager = AccountManager(global_session)
    account_user_manager = AccountUserManager(global_session)
    account_db = AccountDatabase()
    return AccountCreation(account_manager, account_user_manager, account_db)


@pytest.mark.asyncio
class TestAccountCreationCreate:
    async def test_valid_db(
        self, account_create: AccountCreate, account_creation: AccountCreation
    ):
        account = await account_creation.create(account_create)

        assert account.domain == "burgundy.localhost"

        async with get_account_session(account) as session:
            tenant_manager = TenantManager(session)
            tenants = await tenant_manager.list(select(Tenant))

            assert len(tenants) == 1
            tenant = tenants[0]
            assert tenant.default

            client_manager = ClientManager(session)
            clients = await client_manager.list(select(Client))

            assert len(clients) == 1
            client = clients[0]
            assert client.tenant_id == tenant.id

    async def test_user_id(
        self,
        account_create: AccountCreate,
        account_creation: AccountCreation,
        account_admin_user: UserDB,
        global_session: AsyncSession,
    ):
        account = await account_creation.create(account_create, account_admin_user.id)

        account_user_manager = AccountUserManager(global_session)
        account_user = await account_user_manager.get_by_account_and_user(
            account.id, account_admin_user.id
        )
        assert account_user is not None

    async def test_default_parameters(
        self, account_create: AccountCreate, account_creation: AccountCreation
    ):
        account = await account_creation.create(
            account_create,
            default_domain="foobar.fief.dev",
            default_client_id="CLIENT_ID",
            default_client_secret="CLIENT_SECRET",
            default_encryption_key="ENCRYPTION_KEY",
        )

        assert account.domain == "foobar.fief.dev"

        async with get_account_session(account) as session:
            tenant_manager = TenantManager(session)
            tenants = await tenant_manager.list(select(Tenant))

            tenant = tenants[0]
            assert tenant.encrypt_jwk == "ENCRYPTION_KEY"

            client_manager = ClientManager(session)
            clients = await client_manager.list(select(Client))
            client = clients[0]

            assert client.client_id == "CLIENT_ID"
            assert client.client_secret == "CLIENT_SECRET"

    async def test_avoid_domain_collision(
        self, account_create: AccountCreate, account_creation: AccountCreation
    ):
        account_create.name = "Bretagne"
        account = await account_creation.create(account_create)

        assert re.match(r"bretagne-\w+\.localhost", account.domain)
