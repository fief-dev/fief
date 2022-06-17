import contextlib
from typing import TYPE_CHECKING, AsyncGenerator, Dict, Optional

import asyncpg.exceptions
import pymysql.err
from sqlalchemy import exc
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine, AsyncSession

from fief.db.engine import create_engine
from fief.db.types import DatabaseConnectionParameters

if TYPE_CHECKING:
    from fief.models import Workspace


class WorkspaceEngineManager:
    def __init__(self) -> None:
        self.engines: Dict[str, AsyncEngine] = {}

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


workspace_engine_manager = WorkspaceEngineManager()


@contextlib.asynccontextmanager
async def get_connection(
    engine: AsyncEngine, schema_name: Optional[str] = None
) -> AsyncGenerator[AsyncConnection, None]:
    dialect_name = engine.dialect.name
    options = {}
    if dialect_name != "sqlite":
        options["schema_translate_map"] = {None: schema_name}
    try:
        async with engine.connect() as connection:
            yield await connection.execution_options(**options)
    except (
        asyncpg.exceptions.PostgresConnectionError,
        asyncpg.exceptions.InvalidPasswordError,
        OSError,
    ) as e:
        raise ConnectionError from e
    except (exc.OperationalError) as e:
        # Catch MySQL connection error with code 2003
        if isinstance(e.orig, pymysql.err.OperationalError) and e.orig.args[0] == 2003:
            raise ConnectionError from e
        raise


@contextlib.asynccontextmanager
async def get_workspace_session(
    workspace: "Workspace",
) -> AsyncGenerator[AsyncSession, None]:
    engine = workspace_engine_manager.get_engine(
        workspace.get_database_connection_parameters()
    )
    async with get_connection(engine, workspace.get_schema_name()) as connection:
        async with AsyncSession(bind=connection, expire_on_commit=False) as session:
            yield session
