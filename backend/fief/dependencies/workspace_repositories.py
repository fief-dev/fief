from fastapi import Depends

from fief.db import AsyncSession
from fief.dependencies.current_workspace import get_current_workspace_session
from fief.repositories import (
    AuthorizationCodeRepository,
    ClientRepository,
    GrantRepository,
    LoginSessionRepository,
    PermissionRepository,
    RefreshTokenRepository,
    RoleRepository,
    SessionTokenRepository,
    TenantRepository,
    UserFieldRepository,
    UserPermissionRepository,
    UserRepository,
    UserRoleRepository,
    get_repository,
)


async def get_tenant_repository(
    session: AsyncSession = Depends(get_current_workspace_session),
) -> TenantRepository:
    return get_repository(TenantRepository, session)


async def get_client_repository(
    session: AsyncSession = Depends(get_current_workspace_session),
) -> ClientRepository:
    return get_repository(ClientRepository, session)


async def get_user_field_repository(
    session: AsyncSession = Depends(get_current_workspace_session),
) -> UserFieldRepository:
    return get_repository(UserFieldRepository, session)


async def get_user_repository(
    session: AsyncSession = Depends(get_current_workspace_session),
) -> UserRepository:
    return get_repository(UserRepository, session)


async def get_login_session_repository(
    session: AsyncSession = Depends(get_current_workspace_session),
) -> LoginSessionRepository:
    return get_repository(LoginSessionRepository, session)


async def get_authorization_code_repository(
    session: AsyncSession = Depends(get_current_workspace_session),
) -> AuthorizationCodeRepository:
    return get_repository(AuthorizationCodeRepository, session)


async def get_refresh_token_repository(
    session: AsyncSession = Depends(get_current_workspace_session),
) -> RefreshTokenRepository:
    return get_repository(RefreshTokenRepository, session)


async def get_session_token_repository(
    session: AsyncSession = Depends(get_current_workspace_session),
) -> SessionTokenRepository:
    return get_repository(SessionTokenRepository, session)


async def get_grant_repository(
    session: AsyncSession = Depends(get_current_workspace_session),
) -> GrantRepository:
    return get_repository(GrantRepository, session)


async def get_permission_repository(
    session: AsyncSession = Depends(get_current_workspace_session),
) -> PermissionRepository:
    return get_repository(PermissionRepository, session)


async def get_role_repository(
    session: AsyncSession = Depends(get_current_workspace_session),
) -> RoleRepository:
    return get_repository(RoleRepository, session)


async def get_user_permission_repository(
    session: AsyncSession = Depends(get_current_workspace_session),
) -> UserPermissionRepository:
    return get_repository(UserPermissionRepository, session)


async def get_user_role_repository(
    session: AsyncSession = Depends(get_current_workspace_session),
) -> UserRoleRepository:
    return get_repository(UserRoleRepository, session)
