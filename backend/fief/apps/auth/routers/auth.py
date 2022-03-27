from typing import List, Optional

from fastapi import APIRouter, Depends, Query, Request, status
from fastapi.responses import RedirectResponse
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from pydantic import UUID4

from fief.apps.auth.templates import templates
from fief.csrf import check_csrf
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
)
from fief.dependencies.authentication_flow import get_authentication_flow
from fief.dependencies.locale import get_gettext, get_translations
from fief.dependencies.session_token import get_session_token
from fief.dependencies.tenant import get_current_tenant
from fief.dependencies.users import UserManager, get_user_manager
from fief.exceptions import LoginException
from fief.locale import Translations
from fief.models import Client, LoginSession, Tenant
from fief.models.session_token import SessionToken
from fief.schemas.auth import LoginError
from fief.services.authentication_flow import AuthenticationFlow

router = APIRouter(dependencies=[Depends(check_csrf), Depends(get_translations)])


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
    nonce: Optional[str] = Query(None),
    max_age: Optional[int] = Query(None),
    authentication_flow: AuthenticationFlow = Depends(get_authentication_flow),
    session_token: Optional[SessionToken] = Depends(get_session_token),
):
    tenant = client.tenant
    has_valid_session = False
    has_valid_session = session_token is not None and (
        max_age is None or int(session_token.created_at.timestamp()) > max_age
    )

    if has_valid_session and prompt != "login":
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
        nonce=nonce,
        client=client,
    )

    return response


@router.get("/login", name="auth:login.get")
async def get_login(
    request: Request,
    login_session: LoginSession = Depends(get_login_session),
    translations: Translations = Depends(get_translations),
):
    return templates.LocaleTemplateResponse(
        "login.html",
        {"request": request, "tenant": login_session.client.tenant},
        translations=translations,
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
    _=Depends(get_gettext),
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
    translations: Translations = Depends(get_translations),
):
    if session_token is None:
        return RedirectResponse(
            tenant.url_for(request, "auth:login.get"), status_code=status.HTTP_302_FOUND
        )

    if not needs_consent and prompt != "consent":
        user_id = session_token.user_id
        response = await authentication_flow.get_authorization_code_success_redirect(
            login_session.redirect_uri,
            login_session.scope,
            session_token.created_at,
            login_session.state,
            login_session.nonce,
            login_session.client,
            user_id,
        )
        response = await authentication_flow.delete_login_session(
            response, login_session
        )
        return response

    return templates.LocaleTemplateResponse(
        "consent.html",
        {
            "request": request,
            "tenant": login_session.client.tenant,
            "client": login_session.client,
            "scopes": login_session.scope,
        },
        translations=translations,
    )


@router.post("/consent", name="auth:consent.post")
async def post_consent(
    request: Request,
    action: str = Depends(get_consent_action),
    login_session: LoginSession = Depends(get_login_session),
    session_token: Optional[SessionToken] = Depends(get_session_token),
    tenant: Tenant = Depends(get_current_tenant),
    authentication_flow: AuthenticationFlow = Depends(get_authentication_flow),
    _=Depends(get_gettext),
):
    if session_token is None:
        return RedirectResponse(
            tenant.url_for(request, "auth:login.get"), status_code=status.HTTP_302_FOUND
        )

    if action == "allow":
        user_id = session_token.user_id
        await authentication_flow.create_or_update_grant(
            user_id, login_session.client, login_session.scope
        )
        response = await authentication_flow.get_authorization_code_success_redirect(
            login_session.redirect_uri,
            login_session.scope,
            session_token.created_at,
            login_session.state,
            login_session.nonce,
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
