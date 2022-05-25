import json

from fastapi import APIRouter, Depends, Query, Request, status
from fastapi.responses import RedirectResponse

from fief.crypto.token import generate_token
from fief.dependencies.admin_session import get_admin_session_token, get_userinfo
from fief.dependencies.fief import FiefAsyncRelativeEndpoints, get_fief
from fief.dependencies.main_repositories import get_admin_session_token_repository
from fief.models import AdminSessionToken
from fief.repositories import AdminSessionTokenRepository
from fief.settings import settings

router = APIRouter()


@router.get("/login", name="admin.auth:login")
async def login(
    request: Request,
    screen: str = Query("login"),
    fief: FiefAsyncRelativeEndpoints = Depends(get_fief),
):
    url = await fief.auth_url(
        redirect_uri=request.url_for("admin.auth:callback"),
        scope=["openid"],
        extras_params={"screen": screen},
    )
    return RedirectResponse(url=url, status_code=status.HTTP_302_FOUND)


@router.get("/callback", name="admin.auth:callback")
async def callback(
    request: Request,
    code: str = Query(...),
    fief: FiefAsyncRelativeEndpoints = Depends(get_fief),
    repository: AdminSessionTokenRepository = Depends(
        get_admin_session_token_repository
    ),
):
    tokens, userinfo = await fief.auth_callback(
        code, request.url_for("admin.auth:callback")
    )
    token, token_hash = generate_token()
    session_token = AdminSessionToken(
        token=token_hash,
        raw_tokens=json.dumps(tokens),
        raw_userinfo=json.dumps(userinfo),
    )
    await repository.create(session_token)

    response = RedirectResponse(url="/admin/", status_code=status.HTTP_302_FOUND)
    response.set_cookie(
        settings.fief_admin_session_cookie_name,
        token,
        domain=settings.fief_admin_session_cookie_domain,
        secure=settings.fief_admin_session_cookie_secure,
        httponly=True,
    )

    return response


@router.get("/userinfo", name="admin.auth:userinfo")
async def userinfo(userinfo=Depends(get_userinfo)):
    return userinfo


@router.get("/logout", name="admin.auth:logout")
async def logout(
    request: Request,
    session_token: AdminSessionToken = Depends(get_admin_session_token),
    repository: AdminSessionTokenRepository = Depends(
        get_admin_session_token_repository
    ),
):
    await repository.delete(session_token)

    response = RedirectResponse(
        url=f"//{settings.fief_domain}/logout?redirect_uri={request.base_url}admin/",
        status_code=status.HTTP_302_FOUND,
    )
    response.delete_cookie(
        settings.fief_admin_session_cookie_name,
        domain=settings.fief_admin_session_cookie_domain,
        secure=settings.fief_admin_session_cookie_secure,
        httponly=True,
    )

    return response
