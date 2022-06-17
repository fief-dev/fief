from typing import AsyncGenerator

from fief.db.engine import AsyncSession, create_async_session_maker, create_engine
from fief.settings import settings

main_engine = create_engine(settings.get_database_connection_parameters())
main_async_session_maker = create_async_session_maker(main_engine)


async def get_main_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with main_async_session_maker() as session:
        yield session


__all__ = [
    "main_async_session_maker",
    "get_main_async_session",
]
