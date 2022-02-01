import re
from typing import AsyncGenerator

import pytest
from sqlalchemy import select

from fief.db import AsyncSession, get_account_session
from fief.managers import AccountManager, ClientManager, TenantManager
from fief.models import Client, Tenant
from fief.schemas.account import AccountCreate
from fief.services.account_creation import AccountCreation
from fief.services.account_db import AccountDatabase


@pytest.fixture(scope="module")
async def test_database_url(get_test_database) -> AsyncGenerator[str, None]:
    async with get_test_database(name="fief-test-account-creation") as url:
        yield url


@pytest.fixture
def account_create(test_database_url: str) -> AccountCreate:
    return AccountCreate(name="Burgundy", database_url=test_database_url)


@pytest.fixture
def account_creation(global_session: AsyncSession) -> AccountCreation:
    account_manager = AccountManager(global_session)
    account_db = AccountDatabase()
    return AccountCreation(account_manager, account_db)


@pytest.mark.asyncio
class TestAccountCreationCreate:
    async def test_valid_db(
        self, account_create: AccountCreate, account_creation: AccountCreation
    ):
        account = await account_creation.create(account_create)

        assert account.domain == "burgundy.fief.dev"

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

        assert re.match(r"bretagne-\w+\.fief\.dev", account.domain)
