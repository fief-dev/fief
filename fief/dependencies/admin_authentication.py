from fastapi import Depends, HTTPException, Request, status

from fief.dependencies.admin_api_key import get_optional_admin_api_key
from fief.dependencies.admin_session import get_admin_session_token
from fief.dependencies.permission import (
    UserPermissionsGetter,
    get_user_permissions_getter,
)
from fief.models import AdminAPIKey, AdminSessionToken
from fief.repositories import UserRepository
from fief.services.admin import ADMIN_PERMISSION_CODENAME


async def is_authenticated_admin_session(
    request: Request,
    session_token: AdminSessionToken = Depends(get_admin_session_token),
    user_repository: UserRepository = Depends(UserRepository),
    get_user_permissions: UserPermissionsGetter = Depends(get_user_permissions_getter),
):
    user = await user_repository.get_by_id(session_token.user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            headers={"Location": str(request.url_for("dashboard.auth:login"))},
        )

    permissions = await get_user_permissions(user)
    if ADMIN_PERMISSION_CODENAME not in permissions:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    request.state.user_id = str(session_token.user_id)


async def is_authenticated_admin_api(
    admin_api_key: AdminAPIKey | None = Depends(get_optional_admin_api_key),
):
    if admin_api_key is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
