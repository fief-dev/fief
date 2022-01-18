import os
import re
from typing import Generator

import pytest
from sqlalchemy import select

from fief.db import AsyncSession, get_account_session
from fief.managers import AccountManager, ClientManager, TenantManager
from fief.models import Client, Tenant
from fief.schemas.account import AccountCreate
from fief.services.account_creation import AccountCreation
from fief.services.account_db import AccountDatabase


@pytest.fixture
def account_create() -> AccountCreate:
    return AccountCreate(
        name="Burgundy",
        database_url="sqlite:///account.db",
    )


@pytest.fixture
def account_creation(
    global_session: AsyncSession,
) -> Generator[AccountCreation, None, None]:
    account_manager = AccountManager(global_session)
    account_db = AccountDatabase()
    yield AccountCreation(account_manager, account_db)
    try:
        os.remove("account.db")
    except FileNotFoundError:
        pass


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

    async def test_avoid_domain_collision(
        self, account_create: AccountCreate, account_creation: AccountCreation
    ):
        account_create.name = "Bretagne"
        account = await account_creation.create(account_create)

        assert re.match(r"bretagne-\w+\.fief\.dev", account.domain)
