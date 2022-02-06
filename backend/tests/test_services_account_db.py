from typing import AsyncGenerator, Tuple

import pytest
from sqlalchemy import engine, inspect

from fief.db.types import DatabaseType
from fief.services.account_db import AccountDatabase, AccountDatabaseConnectionError


@pytest.fixture
async def test_database_url(
    get_test_database,
) -> AsyncGenerator[Tuple[engine.URL, DatabaseType], None]:
    async with get_test_database(name="fief-test-account-db") as (url, database_type):
        yield url, database_type


@pytest.fixture
def account_db() -> AccountDatabase:
    return AccountDatabase()


class TestMigrate:
    def test_connection_error(self, account_db: AccountDatabase):

        with pytest.raises(AccountDatabaseConnectionError):
            account_db.migrate(
                engine.make_url("postgresql://foo:bar@localhost:1234/foobar"),
                "account-schema",
            )

    def test_valid_db(
        self,
        account_db: AccountDatabase,
        test_database_url: Tuple[engine.URL, DatabaseType],
    ):
        url, _ = test_database_url
        schema = "account_schema"
        account_db.migrate(url, schema)

        engine = account_db.get_engine(url, schema)
        inspector = inspect(engine)

        table_names = inspector.get_table_names()

        assert "fief_alembic_version" in table_names
        assert "fief_tenants" in table_names
