import os
from typing import Generator

import pytest
from sqlalchemy import create_engine, inspect

from fief.models import Account
from fief.services.account_db import AccountDatabase


@pytest.fixture
def account() -> Account:
    return Account(name="Duché de Bretagne", database_url="sqlite:///account.db")


@pytest.fixture
def account_db() -> Generator[AccountDatabase, None, None]:
    yield AccountDatabase()
    os.remove("account.db")


def test_account_db_migrate(account_db: AccountDatabase, account: Account):
    account_db.migrate(account)

    engine = create_engine(account.database_url)
    inspector = inspect(engine)
    table_names = inspector.get_table_names()

    assert "fief_alembic_version" in table_names
    assert "fief_tenants" in table_names
