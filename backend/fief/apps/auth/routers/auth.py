from datetime import datetime, timedelta, timezone
from gettext import gettext as _
from typing import List, Optional, Tuple

from fastapi import APIRouter, Depends, Query, Request, status
from fastapi.responses import RedirectResponse
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from furl import furl
from pydantic import UUID4

from fief.apps.auth.templates import templates
from fief.crypto.access_token import generate_access_token
from fief.crypto.id_token import generate_id_token
from fief.dependencies.account import get_current_account
from fief.dependencies.account_managers import (
    get_authorization_code_manager,
    get_login_session_manager,
    get_refresh_token_manager,
)
from fief.dependencies.auth import (
    get_authorize_client,
    get_authorize_redirect_uri,
    get_authorize_response_type,
    get_authorize_scope,
    get_login_session,
    get_user_from_grant_request,
    validate_grant_request,
)
from fief.dependencies.tenant import get_current_tenant
from fief.dependencies.users import UserManager, get_user_manager
from fief.errors import LoginException
from fief.managers import (
    AuthorizationCodeManager,
    LoginSessionManager,
    RefreshTokenManager,
)
from fief.models import (
    Account,
    AuthorizationCode,
    Client,
    LoginSession,
    RefreshToken,
    Tenant,
)
from fief.schemas.auth import LoginError, TokenResponse
from fief.schemas.user import UserDB
from fief.settings import settings

TOKEN_LIFETIME = 3600
REFRESH_TOKEN_LIFETIME = 3600 * 24 * 30

router = APIRouter()


@router.get("/authorize", name="auth:authorize")
async def authorize(
    request: Request,
    response_type: str = Depends(get_authorize_response_type),
    client: Client = Depends(get_authorize_client),
    redirect_uri: str = Depends(get_authorize_redirect_uri),
    scope: List[str] = Depends(get_authorize_scope),
    state: Optional[str] = Query(None),
    login_session_manager: LoginSessionManager = Depends(get_login_session_manager),
):
    login_session = LoginSession(
        response_type=response_type,
        redirect_uri=redirect_uri,
        scope=scope,
        state=state,
        client_id=client.id,
    )
    login_session = await login_session_manager.create(login_session)

    response = templates.TemplateResponse(
        "authorize.html",
        {"request": request, "tenant": client.tenant},
    )
    response.set_cookie(
        settings.login_session_cookie_name,
        login_session.token,
        domain=settings.login_session_cookie_domain,
        secure=settings.login_session_cookie_secure,
    )

    return response


@router.post("/login", name="auth:login")
async def login(
    credentials: OAuth2PasswordRequestForm = Depends(OAuth2PasswordRequestForm),
    login_session: LoginSession = Depends(get_login_session),
    user_manager: UserManager = Depends(get_user_manager),
    authorization_code_manager: AuthorizationCodeManager = Depends(
        get_authorization_code_manager
    ),
    login_session_manager: LoginSessionManager = Depends(get_login_session_manager),
):
    user = await user_manager.authenticate(credentials)

    if user is None or not user.is_active:
        raise LoginException(
            LoginError.get_bad_credentials(_("Invalid email or password")),
            login_session.client.tenant,
        )
    # if requires_verification and not user.is_verified:
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail=ErrorCode.LOGIN_USER_NOT_VERIFIED,
    #     )

    authorization_code = await authorization_code_manager.create(
        AuthorizationCode(
            redirect_uri=login_session.redirect_uri,
            scope=login_session.scope,
            user_id=user.id,
            client_id=login_session.client.id,
        )
    )

    parsed_redirect_uri = furl(login_session.redirect_uri)
    parsed_redirect_uri.add(query_params={"code": authorization_code.code})
    if login_session.state is not None:
        parsed_redirect_uri.add(query_params={"state": login_session.state})

    response = RedirectResponse(
        url=parsed_redirect_uri.url, status_code=status.HTTP_302_FOUND
    )

    response.delete_cookie(
        settings.login_session_cookie_name, domain=settings.login_session_cookie_domain
    )
    await login_session_manager.delete(login_session)

    return response


@router.post("/token", name="auth:token")
async def token(
    grant_request: Tuple[UUID4, List[str], Client] = Depends(validate_grant_request),
    user: UserDB = Depends(get_user_from_grant_request),
    refresh_token_manager: RefreshTokenManager = Depends(get_refresh_token_manager),
    account: Account = Depends(get_current_account),
    tenant: Tenant = Depends(get_current_tenant),
):
    _, scope, client = grant_request

    tenant_host = tenant.get_host(account.domain)
    access_token = generate_access_token(
        tenant.get_sign_jwk(), tenant_host, client, user, scope, TOKEN_LIFETIME
    )
    id_token = generate_id_token(
        tenant.get_sign_jwk(),
        tenant_host,
        client,
        user,
        TOKEN_LIFETIME,
        encryption_key=tenant.get_encrypt_jwk(),
    )
    token_response = TokenResponse(
        access_token=access_token, id_token=id_token, expires_in=TOKEN_LIFETIME
    )

    if "offline_access" in scope:
        expires_at = datetime.now(timezone.utc) + timedelta(
            seconds=REFRESH_TOKEN_LIFETIME
        )
        refresh_token = RefreshToken(
            expires_at=expires_at, scope=scope, user_id=user.id, client_id=client.id
        )
        refresh_token = await refresh_token_manager.create(refresh_token)
        token_response.refresh_token = refresh_token.token

    return token_response.dict(exclude_none=True)
