from fastapi import Depends

from fief.db import AsyncSession
from fief.db.main import get_main_async_session
from fief.managers import (
    AdminAPIKeyManager,
    AdminSessionTokenManager,
    WorkspaceManager,
    WorkspaceUserManager,
    get_manager,
)


async def get_workspace_manager(
    session: AsyncSession = Depends(get_main_async_session),
) -> WorkspaceManager:
    return get_manager(WorkspaceManager, session)


async def get_admin_session_token_manager(
    session: AsyncSession = Depends(get_main_async_session),
) -> AdminSessionTokenManager:
    return get_manager(AdminSessionTokenManager, session)


async def get_admin_api_key_manager(
    session: AsyncSession = Depends(get_main_async_session),
) -> AdminAPIKeyManager:
    return get_manager(AdminAPIKeyManager, session)


async def get_workspace_user_manager(
    session: AsyncSession = Depends(get_main_async_session),
) -> WorkspaceUserManager:
    return get_manager(WorkspaceUserManager, session)
