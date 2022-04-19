from typing import TYPE_CHECKING

from sqlalchemy import engine, event
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from fief.settings import settings

if TYPE_CHECKING:
    from fief.models import Workspace


def create_engine(database_url: engine.URL) -> AsyncEngine:
    engine = create_async_engine(
        database_url, echo=False and settings.log_level == "DEBUG", pool_recycle=1800
    )
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


def create_async_session_maker(engine: AsyncEngine):
    return sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


__all__ = [
    "create_engine",
    "create_async_session_maker",
]
