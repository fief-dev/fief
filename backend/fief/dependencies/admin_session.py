from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyCookie
from fief_client import FiefUserInfo

from fief.crypto.token import get_token_hash
from fief.dependencies.main_repositories import get_main_repository
from fief.models import AdminSessionToken
from fief.repositories import AdminSessionTokenRepository
from fief.settings import settings

cookie_scheme = APIKeyCookie(
    name=settings.fief_admin_session_cookie_name, auto_error=False
)


async def get_optional_admin_session_token(
    token: Optional[str] = Depends(cookie_scheme),
    repository: AdminSessionTokenRepository = Depends(
        get_main_repository(AdminSessionTokenRepository)
    ),
) -> Optional[AdminSessionToken]:
    if token is None:
        return None
    token_hash = get_token_hash(token)
    session_token = await repository.get_by_token(token_hash)
    return session_token


async def get_admin_session_token(
    admin_session_token: Optional[AdminSessionToken] = Depends(
        get_optional_admin_session_token
    ),
) -> AdminSessionToken:
    if admin_session_token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return admin_session_token


async def get_userinfo(
    session_token: AdminSessionToken = Depends(get_admin_session_token),
) -> FiefUserInfo:
    return session_token.userinfo
