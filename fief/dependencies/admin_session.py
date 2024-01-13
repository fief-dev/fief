from fastapi import Depends, HTTPException, Request, status
from fastapi.security import APIKeyCookie
from fief_client import FiefUserInfo

from fief.crypto.token import get_token_hash
from fief.dependencies.repositories import get_repository
from fief.models import AdminSessionToken
from fief.repositories import AdminSessionTokenRepository
from fief.settings import settings

cookie_scheme = APIKeyCookie(
    name=settings.fief_admin_session_cookie_name, auto_error=False
)


async def get_optional_admin_session_token(
    token: str | None = Depends(cookie_scheme),
    repository: AdminSessionTokenRepository = Depends(
        get_repository(AdminSessionTokenRepository)
    ),
) -> AdminSessionToken | None:
    if token is None:
        return None
    token_hash = get_token_hash(token)
    session_token = await repository.get_by_token(token_hash)
    return session_token


async def get_admin_session_token(
    request: Request,
    admin_session_token: AdminSessionToken | None = Depends(
        get_optional_admin_session_token
    ),
) -> AdminSessionToken:
    if admin_session_token is None:
        raise HTTPException(
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            headers={"Location": str(request.url_for("dashboard.auth:login"))},
        )
    return admin_session_token


async def get_userinfo(
    session_token: AdminSessionToken = Depends(get_admin_session_token),
) -> FiefUserInfo:
    return session_token.userinfo
