import contextlib
import sqlite3
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING, Self

import asyncpg.exceptions
from sqlalchemy import exc
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine, AsyncSession

from fief.db.engine import create_engine
from fief.db.types import DatabaseConnectionParameters

if TYPE_CHECKING:
    from fief.models import Workspace


class WorkspaceEngineManager:
    def __init__(self) -> None:
        self.engines: dict[str, AsyncEngine] = {}

    def get_engine(
        self, database_connection_parameters: DatabaseConnectionParameters
    ) -> AsyncEngine:
        database_url, _ = database_connection_parameters
        key = str(database_url)
        try:
            return self.engines[key]
        except KeyError:
            engine = create_engine(database_connection_parameters)
            self.engines[key] = engine
            return engine

    async def close_all(self):
        for engine in self.engines.values():
            await engine.dispose()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close_all()


@contextlib.asynccontextmanager
async def get_connection(
    engine: AsyncEngine, schema_name: str | None = None
) -> AsyncGenerator[AsyncConnection, None]:
    dialect_name = engine.dialect.name
    options = {}
    if dialect_name != "sqlite":
        options["schema_translate_map"] = {None: schema_name}
    try:
        async with engine.connect() as connection:
            yield await connection.execution_options(**options)
    except exc.OperationalError as e:
        # It turns out that SQLITE_BUSY error can be safely ignored, in particular during tests
        if (
            isinstance(e.orig, sqlite3.OperationalError)
            and e.orig.sqlite_errorcode == sqlite3.SQLITE_BUSY
        ):
            pass
        else:
            raise ConnectionError from e
    except (
        asyncpg.exceptions.PostgresConnectionError,
        asyncpg.exceptions.InvalidAuthorizationSpecificationError,
        OSError,
    ) as e:
        raise ConnectionError from e


@contextlib.asynccontextmanager
async def get_workspace_session(
    workspace: "Workspace",
    workspace_engine_manager: WorkspaceEngineManager,
) -> AsyncGenerator[AsyncSession, None]:
    engine = workspace_engine_manager.get_engine(
        workspace.get_database_connection_parameters()
    )
    async with get_connection(engine, workspace.schema_name) as connection:
        async with AsyncSession(bind=connection, expire_on_commit=False) as session:
            yield session
