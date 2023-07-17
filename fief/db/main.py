import contextlib
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from fief.db.engine import create_async_session_maker, create_engine
from fief.settings import settings


def create_main_engine() -> AsyncEngine:
    return create_engine(settings.get_database_connection_parameters())


def create_main_async_session_maker(engine: AsyncEngine):
    return create_async_session_maker(engine)


@contextlib.asynccontextmanager
async def get_single_main_async_session() -> AsyncGenerator[AsyncSession, None]:
    engine = create_main_engine()
    session_maker = create_async_session_maker(engine)
    async with session_maker() as session:
        yield session
    await engine.dispose()


__all__ = [
    "create_main_engine",
    "create_main_async_session_maker",
    "get_single_main_async_session",
]
