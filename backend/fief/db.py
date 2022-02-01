import contextlib
from functools import lru_cache
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncEngine,
    AsyncSession,
    create_async_engine,
)
from sqlalchemy.orm import sessionmaker

from fief.models import Account
from fief.settings import settings


def create_engine(database_url: str) -> AsyncEngine:
    return create_async_engine(database_url, echo=settings.log_level == "DEBUG")


def create_global_engine() -> AsyncEngine:
    return create_engine(settings.get_database_url())


def create_async_session_maker(engine: AsyncEngine):
    return sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


global_engine = create_global_engine()
global_async_session_maker = create_async_session_maker(global_engine)


async def get_global_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with global_async_session_maker() as session:
        yield session


@lru_cache
def get_account_engine(database_url: str) -> AsyncEngine:
    return create_engine(database_url)


@contextlib.asynccontextmanager
async def get_account_session(account: Account) -> AsyncGenerator[AsyncSession, None]:
    engine = get_account_engine(account.get_database_url())
    async with engine.connect() as connection:
        connection = await connection.execution_options(
            schema_translate_map={None: str(account.id)}
        )
        async with AsyncSession(bind=connection, expire_on_commit=False) as session:
            yield session


__all__ = [
    "AsyncConnection",
    "AsyncEngine",
    "AsyncSession",
    "create_async_session_maker",
    "create_engine",
    "create_global_engine",
    "get_global_async_session",
    "global_async_session_maker",
    "global_engine",
]
