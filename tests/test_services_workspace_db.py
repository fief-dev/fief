import os
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy import engine, inspect
from sqlalchemy.exc import OperationalError

from fief.db.types import DatabaseConnectionParameters, DatabaseType
from fief.services.workspace_db import (
    WorkspaceDatabase,
    WorkspaceDatabaseConnectionError,
)


@pytest_asyncio.fixture
async def test_database_url(
    get_test_database,
) -> AsyncGenerator[tuple[DatabaseConnectionParameters, DatabaseType], None]:
    async with get_test_database(name="fief-test-workspace-db") as (
        database_connection_params,
        database_type,
    ):
        yield database_connection_params, database_type


@pytest.fixture
def workspace_db() -> WorkspaceDatabase:
    return WorkspaceDatabase()


@pytest.mark.asyncio
class TestMigrate:
    async def test_connection_error(self, workspace_db: WorkspaceDatabase):
        with pytest.raises(WorkspaceDatabaseConnectionError):
            workspace_db.migrate(
                (engine.make_url("postgresql://foo:bar@localhost:1234/foobar"), {}),
                "fief_",
                "workspace-schema",
            )

    async def test_valid_db(
        self,
        workspace_db: WorkspaceDatabase,
        test_database_url: tuple[DatabaseConnectionParameters, DatabaseType],
    ):
        database_connection_params, _ = test_database_url
        schema = "workspace_schema"
        workspace_db.migrate(database_connection_params, "fief_", schema)

        with workspace_db._get_engine(database_connection_params, schema) as engine:
            inspector = inspect(engine)
            table_names = inspector.get_table_names()
            assert "fief_alembic_version" in table_names
            assert "fief_tenants" in table_names


@pytest.mark.asyncio
class TestDrop:
    async def test_connection_error(self, workspace_db: WorkspaceDatabase):
        with pytest.raises(WorkspaceDatabaseConnectionError):
            workspace_db.drop(
                (engine.make_url("postgresql://foo:bar@localhost:1234/foobar"), {}),
                "workspace-schema",
            )

    async def test_valid_db(
        self,
        workspace_db: WorkspaceDatabase,
        test_database_url: tuple[DatabaseConnectionParameters, DatabaseType],
    ):
        database_connection_params, database_type = test_database_url
        schema = "workspace_schema"
        workspace_db.migrate(database_connection_params, "fief_", schema)

        workspace_db.drop(database_connection_params, schema)

        if database_type == DatabaseType.SQLITE:
            url, _ = database_connection_params
            assert url.database is not None
            assert not os.path.exists(url.database)
        elif database_type == DatabaseType.POSTGRESQL:
            with workspace_db._get_engine(database_connection_params, schema) as engine:
                inspector = inspect(engine)
                schemas = inspector.get_schema_names()
                assert schema not in schemas
        elif database_type == DatabaseType.MYSQL:
            with pytest.raises(OperationalError) as e:
                with workspace_db._get_engine(
                    database_connection_params, schema
                ) as engine:
                    engine.connect()
            assert "Unknown database" in str(e.value.orig)


@pytest.mark.asyncio
class TestCheckConnection:
    async def test_invalid(self, workspace_db: WorkspaceDatabase):
        valid, message = workspace_db.check_connection(
            (engine.make_url("postgresql://foo:bar@localhost:1234/foobar"), {}),
        )

        assert valid is False
        assert message is not None
        assert "Connection refused" in message

    async def test_valid_db(
        self,
        workspace_db: WorkspaceDatabase,
        test_database_url: tuple[DatabaseConnectionParameters, DatabaseType],
    ):
        database_connection_params, _ = test_database_url
        valid, message = workspace_db.check_connection(database_connection_params)

        assert valid
        assert message is None
