from typing import AsyncGenerator

import pytest
from sqlalchemy import create_engine, inspect

from fief.models import Account
from fief.services.account_db import AccountDatabase, AccountDatabaseConnectionError


@pytest.fixture
async def test_database_url(get_test_database) -> AsyncGenerator[str, None]:
    async with get_test_database(name="fief-test-account-db") as url:
        yield url


@pytest.fixture
def account_db() -> AccountDatabase:
    return AccountDatabase()


class TestMigrate:
    def test_connection_error(self, account_db: AccountDatabase):

        with pytest.raises(AccountDatabaseConnectionError):
            account_db.migrate(
                "postgresql://foo:bar@localhost:1234/foobar", "account-schema"
            )

    def test_valid_db(self, account_db: AccountDatabase, test_database_url: str):
        account_db.migrate(test_database_url, "account-schema")

        engine = create_engine(test_database_url)
        inspector = inspect(engine)
        table_names = inspector.get_table_names("account-schema")

        assert "fief_alembic_version" in table_names
        assert "fief_tenants" in table_names
