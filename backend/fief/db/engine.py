import contextlib
from typing import TYPE_CHECKING, AsyncGenerator, Dict, Optional

from sqlalchemy import engine, event
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncEngine,
    AsyncSession,
    create_async_engine,
)
from sqlalchemy.orm import sessionmaker

from fief.settings import settings

if TYPE_CHECKING:
    from fief.models import Account


def create_engine(database_url: engine.URL) -> AsyncEngine:
    engine = create_async_engine(database_url, echo=settings.log_level == "DEBUG")
    dialect_name = engine.dialect.name

    # Special tweak for SQLite to better handle transaction
    # See: https://docs.sqlalchemy.org/en/14/dialects/sqlite.html#serializable-isolation-savepoints-transactional-ddl
    if dialect_name == "sqlite":

        @event.listens_for(engine.sync_engine, "connect")
        def do_connect(dbapi_connection, connection_record):
            # disable pysqlite's emitting of the BEGIN statement entirely.
            # also stops it from emitting COMMIT before any DDL.
            dbapi_connection.isolation_level = None

        @event.listens_for(engine.sync_engine, "begin")
        def do_begin(conn):
            # emit our own BEGIN
            conn.exec_driver_sql("BEGIN")

    return engine


def create_global_engine() -> AsyncEngine:
    return create_engine(settings.get_database_url())


def create_async_session_maker(engine: AsyncEngine):
    return sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


global_engine = create_global_engine()
global_async_session_maker = create_async_session_maker(global_engine)


async def get_global_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with global_async_session_maker() as session:
        yield session


class AccountEngineManager:
    def __init__(self) -> None:
        self.engines: Dict[str, AsyncEngine] = {}

    def get_engine(self, database_url: engine.URL) -> AsyncEngine:
        key = str(database_url)
        try:
            return self.engines[key]
        except KeyError:
            engine = create_engine(database_url)
            self.engines[key] = engine
            return engine

    async def close_all(self):
        for engine in self.engines.values():
            await engine.dispose()


account_engine_manager = AccountEngineManager()


@contextlib.asynccontextmanager
async def get_connection(
    engine: AsyncEngine, schema_name: Optional[str] = None
) -> AsyncGenerator[AsyncConnection, None]:
    dialect_name = engine.dialect.name
    options = {}
    if dialect_name != "sqlite":
        options["schema_translate_map"] = {None: schema_name}
    async with engine.connect() as connection:
        yield await connection.execution_options(**options)


@contextlib.asynccontextmanager
async def get_account_session(account: "Account") -> AsyncGenerator[AsyncSession, None]:
    engine = account_engine_manager.get_engine(account.get_database_url())
    async with get_connection(engine, account.get_schema_name()) as connection:
        async with AsyncSession(bind=connection, expire_on_commit=False) as session:
            yield session
