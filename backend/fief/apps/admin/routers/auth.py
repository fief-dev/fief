import json

from fastapi import APIRouter, Depends, Query, Request, status
from fastapi.responses import RedirectResponse
from fief_client import FiefAsync
from furl import furl

from fief.dependencies.admin_session import get_userinfo
from fief.dependencies.fief import get_fief
from fief.dependencies.main_managers import get_admin_session_token_manager
from fief.managers import AdminSessionTokenManager
from fief.models import AdminSessionToken
from fief.settings import settings

router = APIRouter()


@router.get("/login", name="admin.auth:login")
async def login(request: Request, fief: FiefAsync = Depends(get_fief)):
    url = await fief.auth_url(
        redirect_uri=request.url_for("admin.auth:callback"), scope=["openid"]
    )

    # Tweak the URL manually to avoid issues when running on different ports.
    # Typically, the Fief client will be queried internally on http://localhost
    # Thus, it'll return URL with this base.
    # However, when running locally (e.g. Docker), it's common
    # to expose the server on a different port, like http://localhost:8000.
    # By replacing the port by the one of the request, we make sure
    # to have a working redirection.
    parsed_url = furl(url)
    parsed_url.port = request.base_url.port

    return RedirectResponse(url=parsed_url.url, status_code=status.HTTP_302_FOUND)


@router.get("/callback", name="admin.auth:callback")
async def callback(
    request: Request,
    code: str = Query(...),
    fief: FiefAsync = Depends(get_fief),
    manager: AdminSessionTokenManager = Depends(get_admin_session_token_manager),
):
    tokens, userinfo = await fief.auth_callback(
        code, request.url_for("admin.auth:callback")
    )
    session_token = AdminSessionToken(
        raw_tokens=json.dumps(tokens), raw_userinfo=json.dumps(userinfo)
    )
    session_token = await manager.create(session_token)

    response = RedirectResponse(url="/admin/", status_code=status.HTTP_302_FOUND)
    response.set_cookie(
        settings.fief_admin_session_cookie_name,
        session_token.token,
        domain=settings.fief_admin_session_cookie_domain,
        secure=settings.fief_admin_session_cookie_secure,
        httponly=True,
    )

    return response


@router.get("/userinfo", name="admin.auth:userinfo")
async def userinfo(userinfo=Depends(get_userinfo)):
    return userinfo
