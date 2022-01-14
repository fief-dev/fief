import os
from typing import Generator

import pytest
from sqlalchemy import create_engine, inspect

from fief.models import Account
from fief.services.account_db import AccountDatabase


@pytest.fixture
def local_account() -> Account:
    return Account(
        name="Duché de Bretagne",
        domain="bretagne.fief.dev",
        database_url="sqlite:///account.db",
    )


@pytest.fixture
def account_db() -> Generator[AccountDatabase, None, None]:
    yield AccountDatabase()
    os.remove("account.db")


def test_account_db_migrate(account_db: AccountDatabase, local_account: Account):
    account_db.migrate(local_account)

    engine = create_engine(local_account.get_database_url(asyncio=False))
    inspector = inspect(engine)
    table_names = inspector.get_table_names()

    assert "fief_alembic_version" in table_names
    assert "fief_tenants" in table_names
