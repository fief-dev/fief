from typing import AsyncGenerator, Tuple

import pytest
from sqlalchemy import engine, inspect

from fief.db.types import DatabaseType
from fief.services.workspace_db import (
    WorkspaceDatabase,
    WorkspaceDatabaseConnectionError,
)


@pytest.fixture
async def test_database_url(
    get_test_database,
) -> AsyncGenerator[Tuple[engine.URL, DatabaseType], None]:
    async with get_test_database(name="fief-test-workspace-db") as (url, database_type):
        yield url, database_type


@pytest.fixture
def workspace_db() -> WorkspaceDatabase:
    return WorkspaceDatabase()


@pytest.mark.asyncio
class TestMigrate:
    async def test_connection_error(self, workspace_db: WorkspaceDatabase):

        with pytest.raises(WorkspaceDatabaseConnectionError):
            workspace_db.migrate(
                engine.make_url("postgresql://foo:bar@localhost:1234/foobar"),
                "workspace-schema",
            )

    async def test_valid_db(
        self,
        workspace_db: WorkspaceDatabase,
        test_database_url: Tuple[engine.URL, DatabaseType],
    ):
        url, _ = test_database_url
        schema = "workspace_schema"
        workspace_db.migrate(url, schema)

        engine = workspace_db.get_engine(url, schema)
        inspector = inspect(engine)

        table_names = inspector.get_table_names()

        assert "fief_alembic_version" in table_names
        assert "fief_tenants" in table_names


@pytest.mark.asyncio
class TestCheckConnection:
    async def test_invalid(self, workspace_db: WorkspaceDatabase):
        valid, message = workspace_db.check_connection(
            engine.make_url("postgresql://foo:bar@localhost:1234/foobar")
        )

        assert valid is False
        assert message is not None
        assert "Connection refused" in message

    async def test_valid_db(
        self,
        workspace_db: WorkspaceDatabase,
        test_database_url: Tuple[engine.URL, DatabaseType],
    ):
        url, _ = test_database_url
        valid, message = workspace_db.check_connection(url)

        assert valid
        assert message is None
