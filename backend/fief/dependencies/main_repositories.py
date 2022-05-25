from fastapi import Depends

from fief.db import AsyncSession
from fief.db.main import get_main_async_session
from fief.repositories import (
    AdminAPIKeyRepository,
    AdminSessionTokenRepository,
    WorkspaceRepository,
    WorkspaceUserRepository,
    get_repository,
)


async def get_workspace_repository(
    session: AsyncSession = Depends(get_main_async_session),
) -> WorkspaceRepository:
    return get_repository(WorkspaceRepository, session)


async def get_admin_session_token_repository(
    session: AsyncSession = Depends(get_main_async_session),
) -> AdminSessionTokenRepository:
    return get_repository(AdminSessionTokenRepository, session)


async def get_admin_api_key_repository(
    session: AsyncSession = Depends(get_main_async_session),
) -> AdminAPIKeyRepository:
    return get_repository(AdminAPIKeyRepository, session)


async def get_workspace_user_repository(
    session: AsyncSession = Depends(get_main_async_session),
) -> WorkspaceUserRepository:
    return get_repository(WorkspaceUserRepository, session)
