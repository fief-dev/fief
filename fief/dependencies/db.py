from collections.abc import AsyncGenerator

from fastapi import Request

from fief.db import AsyncSession
from fief.db.workspace import WorkspaceEngineManager


async def get_workspace_engine_manager(request: Request) -> WorkspaceEngineManager:
    return request.state.workspace_engine_manager


async def get_main_async_session(
    request: Request,
) -> AsyncGenerator[AsyncSession, None]:
    async with request.state.main_async_session_maker() as session:
        yield session
