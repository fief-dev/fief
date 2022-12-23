from collections.abc import AsyncGenerator

from fief.db import AsyncSession
from fief.db.main import create_main_async_session_maker
from fief.db.workspace import WorkspaceEngineManager

workspace_engine_manager = WorkspaceEngineManager()
main_async_session_maker = create_main_async_session_maker()


async def get_workspace_engine_manager() -> WorkspaceEngineManager:
    return workspace_engine_manager


async def get_main_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with main_async_session_maker() as session:
        yield session
