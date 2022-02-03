from datetime import datetime, timedelta, timezone
from gettext import gettext as _
from typing import List, Optional, Tuple, cast

from fastapi import APIRouter, Depends, Query, Request, status
from fastapi.responses import RedirectResponse
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from pydantic import UUID4

from fief.apps.auth.templates import templates
from fief.crypto.access_token import generate_access_token
from fief.crypto.id_token import generate_id_token
from fief.dependencies.account import get_current_account
from fief.dependencies.account_managers import (
    get_login_session_manager,
    get_refresh_token_manager,
)
from fief.dependencies.auth import (
    get_authorize_client,
    get_authorize_prompt,
    get_authorize_redirect_uri,
    get_authorize_response_type,
    get_authorize_scope,
    get_authorize_screen,
    get_consent_action,
    get_consent_prompt,
    get_login_session,
    get_needs_consent,
    get_user_from_grant_request,
    validate_grant_request,
)
from fief.dependencies.authentication_flow import get_authentication_flow
from fief.dependencies.session_token import get_session_token
from fief.dependencies.tenant import get_current_tenant
from fief.dependencies.users import UserManager, get_user_manager
from fief.errors import LoginException
from fief.managers import RefreshTokenManager
from fief.models import Account, Client, LoginSession, RefreshToken, Tenant
from fief.models.session_token import SessionToken
from fief.schemas.auth import LoginError, TokenResponse
from fief.schemas.user import UserDB
from fief.services.authentication_flow import AuthenticationFlow

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
    prompt: Optional[str] = Depends(get_authorize_prompt),
    screen: str = Depends(get_authorize_screen),
    state: Optional[str] = Query(None),
    authentication_flow: AuthenticationFlow = Depends(get_authentication_flow),
    session_token: Optional[SessionToken] = Depends(get_session_token),
):
    tenant = client.tenant
    if session_token is not None and prompt != "login":
        redirection = tenant.url_for(request, "auth:consent.get")
    elif screen == "register":
        redirection = tenant.url_for(request, "register:get")
    else:
        redirection = tenant.url_for(request, "auth:login.get")

    response = RedirectResponse(url=redirection, status_code=status.HTTP_302_FOUND)
    response = await authentication_flow.create_login_session(
        response,
        response_type=response_type,
        redirect_uri=redirect_uri,
        scope=scope,
        state=state,
        client=client,
    )

    return response


@router.get("/login", name="auth:login.get")
async def get_login(
    request: Request, login_session: LoginSession = Depends(get_login_session)
):
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "tenant": login_session.client.tenant},
    )


@router.post("/login", name="auth:login.post")
async def post_login(
    request: Request,
    credentials: OAuth2PasswordRequestForm = Depends(OAuth2PasswordRequestForm),
    login_session: LoginSession = Depends(get_login_session),
    user_manager: UserManager = Depends(get_user_manager),
    authentication_flow: AuthenticationFlow = Depends(get_authentication_flow),
    session_token: Optional[SessionToken] = Depends(get_session_token),
    tenant: Tenant = Depends(get_current_tenant),
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

    response = RedirectResponse(
        tenant.url_for(request, "auth:consent.get"),
        status_code=status.HTTP_302_FOUND,
    )
    if session_token is None:
        response = await authentication_flow.create_session_token(response, user.id)

    return response


@router.get("/consent", name="auth:consent.get")
async def get_consent(
    request: Request,
    login_session: LoginSession = Depends(get_login_session),
    session_token: Optional[SessionToken] = Depends(get_session_token),
    prompt: Optional[str] = Depends(get_consent_prompt),
    needs_consent: bool = Depends(get_needs_consent),
    tenant: Tenant = Depends(get_current_tenant),
    authentication_flow: AuthenticationFlow = Depends(get_authentication_flow),
):
    if session_token is None:
        return RedirectResponse(
            tenant.url_for(request, "auth:login.get"), status_code=status.HTTP_302_FOUND
        )

    if not needs_consent and prompt != "consent":
        user_id = cast(UUID4, session_token.user_id)
        response = await authentication_flow.get_authorization_code_success_redirect(
            login_session.redirect_uri,
            login_session.scope,
            login_session.state,
            login_session.client,
            user_id,
        )
        response = await authentication_flow.delete_login_session(
            response, login_session
        )
        return response

    return templates.TemplateResponse(
        "consent.html",
        {
            "request": request,
            "tenant": login_session.client.tenant,
            "client": login_session.client,
            "scopes": login_session.scope,
        },
    )


@router.post("/consent", name="auth:consent.post")
async def post_consent(
    request: Request,
    action: str = Depends(get_consent_action),
    login_session: LoginSession = Depends(get_login_session),
    session_token: Optional[SessionToken] = Depends(get_session_token),
    tenant: Tenant = Depends(get_current_tenant),
    authentication_flow: AuthenticationFlow = Depends(get_authentication_flow),
):
    if session_token is None:
        return RedirectResponse(
            tenant.url_for(request, "auth:login.get"), status_code=status.HTTP_302_FOUND
        )

    if action == "allow":
        user_id = cast(UUID4, session_token.user_id)
        await authentication_flow.create_or_update_grant(
            user_id, login_session.client, login_session.scope
        )
        response = await authentication_flow.get_authorization_code_success_redirect(
            login_session.redirect_uri,
            login_session.scope,
            login_session.state,
            login_session.client,
            user_id,
        )
    elif action == "deny":
        response = AuthenticationFlow.get_authorization_code_error_redirect(
            login_session.redirect_uri,
            "access_denied",
            error_description=_("The user denied access to their data."),
            state=login_session.state,
        )

    response = await authentication_flow.delete_login_session(response, login_session)

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
