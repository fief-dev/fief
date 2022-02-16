from typing import Any, Dict, Optional

from fastapi import Cookie, Depends, HTTPException, status
from fastapi.security import APIKeyCookie
from pydantic import UUID4

from fief.dependencies.global_managers import (
    get_account_user_manager,
    get_admin_session_token_manager,
)
from fief.managers import AccountUserManager, AdminSessionTokenManager
from fief.models import Account, AdminSessionToken
from fief.settings import settings

cookie_scheme = APIKeyCookie(
    name=settings.fief_admin_session_cookie_name, auto_error=False
)


async def get_optional_admin_session_token(
    token: Optional[str] = Depends(cookie_scheme),
    manager: AdminSessionTokenManager = Depends(get_admin_session_token_manager),
) -> Optional[AdminSessionToken]:
    if token is None:
        return None
    session_token = await manager.get_by_token(token)
    return session_token


async def get_admin_session_token(
    admin_session_token: Optional[AdminSessionToken] = Depends(
        get_optional_admin_session_token
    ),
) -> AdminSessionToken:
    if admin_session_token is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return admin_session_token


async def get_account_from_admin_session(
    fief_account_id: Optional[UUID4] = Cookie(None),
    admin_session_token: Optional[AdminSessionToken] = Depends(
        get_optional_admin_session_token
    ),
    account_user_manager: AccountUserManager = Depends(get_account_user_manager),
) -> Optional[Account]:
    if fief_account_id is None or admin_session_token is None:
        return None

    account_user = await account_user_manager.get_by_account_and_user(
        fief_account_id, admin_session_token.user_id
    )

    if account_user is None:
        return None

    return account_user.account


async def get_userinfo(
    session_token: AdminSessionToken = Depends(get_admin_session_token),
) -> Dict[str, Any]:
    return session_token.userinfo
