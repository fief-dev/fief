import os
from typing import Generator

import pytest
from sqlalchemy import create_engine, inspect

from fief.models import Account
from fief.services.account_db import AccountDatabase, AccountDatabaseConnectionError


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
    try:
        os.remove("account.db")
    except FileNotFoundError:
        pass


class TestMigrate:
    def test_connection_error(
        self, account_db: AccountDatabase, local_account: Account
    ):
        local_account.database_url = "postgresql://foo:bar@localhost:1234/foobar"

        with pytest.raises(AccountDatabaseConnectionError):
            account_db.migrate(local_account)

    def test_valid_db(self, account_db: AccountDatabase, local_account: Account):
        account_db.migrate(local_account)

        engine = create_engine(local_account.get_database_url(asyncio=False))
        inspector = inspect(engine)
        table_names = inspector.get_table_names()

        assert "fief_alembic_version" in table_names
        assert "fief_tenants" in table_names
