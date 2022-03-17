from fastapi import Depends

from fief.db import AsyncSession
from fief.dependencies.current_workspace import get_current_workspace_session
from fief.managers import (
    AuthorizationCodeManager,
    ClientManager,
    GrantManager,
    LoginSessionManager,
    RefreshTokenManager,
    SessionTokenManager,
    TenantManager,
    UserManager,
    get_manager,
)


async def get_tenant_manager(
    session: AsyncSession = Depends(get_current_workspace_session),
) -> TenantManager:
    return get_manager(TenantManager, session)


async def get_client_manager(
    session: AsyncSession = Depends(get_current_workspace_session),
) -> ClientManager:
    return get_manager(ClientManager, session)


async def get_user_manager(
    session: AsyncSession = Depends(get_current_workspace_session),
) -> UserManager:
    return get_manager(UserManager, session)


async def get_login_session_manager(
    session: AsyncSession = Depends(get_current_workspace_session),
) -> LoginSessionManager:
    return get_manager(LoginSessionManager, session)


async def get_authorization_code_manager(
    session: AsyncSession = Depends(get_current_workspace_session),
) -> AuthorizationCodeManager:
    return get_manager(AuthorizationCodeManager, session)


async def get_refresh_token_manager(
    session: AsyncSession = Depends(get_current_workspace_session),
) -> RefreshTokenManager:
    return get_manager(RefreshTokenManager, session)


async def get_session_token_manager(
    session: AsyncSession = Depends(get_current_workspace_session),
) -> SessionTokenManager:
    return get_manager(SessionTokenManager, session)


async def get_grant_manager(
    session: AsyncSession = Depends(get_current_workspace_session),
) -> GrantManager:
    return get_manager(GrantManager, session)
