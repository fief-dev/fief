from typing import Any, Dict

from fastapi import Depends, HTTPException, status
from fastapi.security import APIKeyCookie
from fief_client import FiefAsync

from fief.dependencies.global_managers import get_admin_session_token_manager
from fief.managers import AdminSessionTokenManager
from fief.models import AdminSessionToken
from fief.settings import settings

fief = FiefAsync(
    settings.fief_base_url,
    settings.fief_client_id,
    settings.fief_client_secret,
    encryption_key=settings.fief_encryption_key,
    host=settings.fief_domain,
)


async def get_fief() -> FiefAsync:
    """
    This is Fief-ception.

    We are configuring a Fief client to authenticate Fief users to their account.
    """
    return fief


cookie_scheme = APIKeyCookie(name=settings.fief_admin_session_cookie_name)


async def get_cookie_session_token(
    token: str = Depends(cookie_scheme),
    manager: AdminSessionTokenManager = Depends(get_admin_session_token_manager),
) -> AdminSessionToken:
    session_token = await manager.get_by_token(token)

    if session_token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    return session_token


async def get_userinfo(
    session_token: AdminSessionToken = Depends(get_cookie_session_token),
) -> Dict[str, Any]:
    return session_token.userinfo
