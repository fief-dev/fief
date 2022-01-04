from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from fief.settings import settings


def create_engine(database_url: str) -> AsyncEngine:
    return create_async_engine(database_url, echo=False)


def create_global_engine() -> AsyncEngine:
    return create_engine(settings.get_database_url())


def create_async_session_maker(engine: AsyncEngine):
    return sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


global_engine = create_global_engine()
global_async_session_maker = create_async_session_maker(global_engine)


async def get_global_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with global_async_session_maker() as session:
        yield session


__all__ = [
    "AsyncEngine",
    "AsyncSession",
    "create_async_session_maker",
    "create_engine",
    "create_global_engine",
    "get_global_async_session",
    "global_async_session_maker",
    "global_engine",
]
