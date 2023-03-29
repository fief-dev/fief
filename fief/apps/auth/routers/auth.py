import urllib.parse

from fastapi import APIRouter, Depends, Query, Request, status
from fastapi.responses import RedirectResponse
from pydantic import AnyUrl

from fief.apps.auth.forms.auth import ConsentForm, LoginForm
from fief.dependencies.auth import (
    check_unsupported_request_parameter,
    get_authorize_client,
    get_authorize_code_challenge,
    get_authorize_prompt,
    get_authorize_redirect_uri,
    get_authorize_response_mode,
    get_authorize_response_type,
    get_authorize_scope,
    get_authorize_screen,
    get_consent_prompt,
    get_login_session,
    get_needs_consent,
    get_nonce,
    get_optional_login_session,
    has_valid_session_token,
)
from fief.dependencies.authentication_flow import get_authentication_flow
from fief.dependencies.current_workspace import get_current_workspace
from fief.dependencies.login_hint import LoginHint, get_login_hint
from fief.dependencies.oauth_provider import get_oauth_providers
from fief.dependencies.session_token import get_session_token
from fief.dependencies.tenant import get_current_tenant
from fief.dependencies.theme import get_current_theme
from fief.dependencies.users import UserManager, get_user_manager
from fief.dependencies.workspace_repositories import get_workspace_repository
from fief.exceptions import LogoutException
from fief.forms import FormHelper
from fief.locale import gettext_lazy as _
from fief.models import Client, LoginSession, OAuthProvider, Tenant, Theme, Workspace
from fief.models.session_token import SessionToken
from fief.repositories.session_token import SessionTokenRepository
from fief.schemas.auth import LogoutError
from fief.services.authentication_flow import AuthenticationFlow
from fief.settings import settings

router = APIRouter()


@router.get(
    "/authorize",
    name="auth:authorize",
    dependencies=[Depends(check_unsupported_request_parameter)],
)
async def authorize(
    request: Request,
    response_type: str = Depends(get_authorize_response_type),
    client: Client = Depends(get_authorize_client),
    redirect_uri: str = Depends(get_authorize_redirect_uri),
    response_mode: str = Depends(get_authorize_response_mode),
    scope: list[str] = Depends(get_authorize_scope),
    prompt: str | None = Depends(get_authorize_prompt),
    screen: str = Depends(get_authorize_screen),
    code_challenge_tuple: tuple[str, str]
    | None = Depends(get_authorize_code_challenge),
    nonce: str | None = Depends(get_nonce),
    state: str | None = Query(None),
    login_hint: str | None = Query(None),
    lang: str | None = Query(None),
    authentication_flow: AuthenticationFlow = Depends(get_authentication_flow),
    has_valid_session_token: bool = Depends(has_valid_session_token),
):
    tenant = client.tenant

    if has_valid_session_token and prompt != "login":
        redirection = tenant.url_path_for(request, "auth:consent")
    elif screen == "register":
        redirection = tenant.url_path_for(request, "register:register")
    else:
        redirection = tenant.url_path_for(request, "auth:login")

    response = RedirectResponse(url=redirection, status_code=status.HTTP_302_FOUND)
    response = await authentication_flow.create_login_session(
        response,
        response_type=response_type,
        response_mode=response_mode,
        redirect_uri=redirect_uri,
        scope=scope,
        state=state,
        nonce=nonce,
        code_challenge_tuple=code_challenge_tuple,
        client=client,
    )

    if login_hint is not None:
        response.set_cookie(
            settings.login_hint_cookie_name,
            urllib.parse.quote(login_hint),
            max_age=settings.login_hint_cookie_lifetime_seconds,
            domain=settings.login_hint_cookie_domain,
            secure=settings.login_hint_cookie_secure,
            httponly=True,
        )

    if lang is not None:
        response.set_cookie(
            settings.user_locale_cookie_name,
            lang,
            max_age=settings.user_locale_lifetime_seconds,
            domain=settings.session_cookie_domain,
            secure=settings.session_cookie_secure,
            httponly=True,
        )

    return response


@router.api_route("/login", methods=["GET", "POST"], name="auth:login")
async def login(
    request: Request,
    login_session: LoginSession | None = Depends(get_optional_login_session),
    user_manager: UserManager = Depends(get_user_manager),
    authentication_flow: AuthenticationFlow = Depends(get_authentication_flow),
    session_token: SessionToken | None = Depends(get_session_token),
    oauth_providers: list[OAuthProvider] = Depends(get_oauth_providers),
    login_hint: LoginHint | None = Depends(get_login_hint),
    tenant: Tenant = Depends(get_current_tenant),
    theme: Theme = Depends(get_current_theme),
):
    # Prefill email with login_hint if it's a string
    initial_form_data = None
    if isinstance(login_hint, str):
        initial_form_data = {"email": login_hint}

    form_helper = FormHelper(
        LoginForm,
        "auth/login.html",
        request=request,
        data=initial_form_data,
        context={
            "oauth_providers": oauth_providers,
            "oauth_provider_login_hint": login_hint
            if isinstance(login_hint, OAuthProvider)
            else None,
            "tenant": tenant,
            "theme": theme,
        },
    )
    form = await form_helper.get_form()

    if await form_helper.is_submitted_and_valid():
        user = await user_manager.authenticate(form.get_credentials())
        if user is None or not user.is_active:
            return await form_helper.get_error_response(
                _("Invalid email or password"), "bad_credentials"
            )

        if login_session is not None:
            response = RedirectResponse(
                tenant.url_path_for(request, "auth:consent"),
                status_code=status.HTTP_302_FOUND,
            )
        else:
            response = RedirectResponse(
                tenant.url_path_for(request, "auth.dashboard:profile"),
                status_code=status.HTTP_302_FOUND,
            )

        response = await authentication_flow.rotate_session_token(
            response, user.id, session_token=session_token
        )
        response = await authentication_flow.set_login_hint(response, str(user.email))

        return response

    return await form_helper.get_response()


@router.api_route("/consent", methods=["GET", "POST"], name="auth:consent")
async def consent(
    request: Request,
    login_session: LoginSession = Depends(get_login_session),
    session_token: SessionToken | None = Depends(get_session_token),
    prompt: str | None = Depends(get_consent_prompt),
    needs_consent: bool = Depends(get_needs_consent),
    tenant: Tenant = Depends(get_current_tenant),
    theme: Theme = Depends(get_current_theme),
    workspace: Workspace = Depends(get_current_workspace),
    authentication_flow: AuthenticationFlow = Depends(get_authentication_flow),
):
    form_helper = FormHelper(
        ConsentForm,
        "auth/consent.html",
        request=request,
        context={
            "tenant": tenant,
            "theme": theme,
            "client": login_session.client,
            "scopes": login_session.scope,
        },
    )
    form = await form_helper.get_form()

    if session_token is None:
        return RedirectResponse(
            tenant.url_path_for(request, "auth:login"),
            status_code=status.HTTP_302_FOUND,
        )

    if not needs_consent and prompt != "consent":
        response = await authentication_flow.get_authorization_code_success_redirect(
            login_session=login_session,
            authenticated_at=session_token.created_at,
            user=session_token.user,
            client=login_session.client,
            tenant=tenant,
            workspace=workspace,
        )
        response = await authentication_flow.delete_login_session(
            response, login_session
        )
        return response

    if await form_helper.is_submitted_and_valid():
        # Allow
        if form.allow.data:
            user_id = session_token.user_id
            await authentication_flow.create_or_update_grant(
                user_id, login_session.client, login_session.scope
            )
            response = (
                await authentication_flow.get_authorization_code_success_redirect(
                    login_session=login_session,
                    authenticated_at=session_token.created_at,
                    user=session_token.user,
                    client=login_session.client,
                    tenant=tenant,
                    workspace=workspace,
                )
            )
        # Deny
        elif form.deny.data:
            response = AuthenticationFlow.get_authorization_code_error_redirect(
                login_session.redirect_uri,
                login_session.response_mode,
                "access_denied",
                error_description=_("The user denied access to their data."),
                state=login_session.state,
            )

        response = await authentication_flow.delete_login_session(
            response, login_session
        )
        return response

    return await form_helper.get_response()


@router.get("/logout", name="auth:logout")
async def logout(
    redirect_uri: AnyUrl | None = Query(None),
    session_token: SessionToken | None = Depends(get_session_token),
    sesstion_token_repository: SessionTokenRepository = Depends(
        get_workspace_repository(SessionTokenRepository)
    ),
    tenant: Tenant = Depends(get_current_tenant),
):
    if redirect_uri is None:
        raise LogoutException(
            LogoutError.get_invalid_request(_("redirect_uri is missing")),
            tenant,
        )

    if session_token is not None:
        await sesstion_token_repository.delete(session_token)

    response = RedirectResponse(redirect_uri, status_code=status.HTTP_302_FOUND)

    response.delete_cookie(
        settings.session_cookie_name,
        domain=settings.session_cookie_domain,
        secure=settings.session_cookie_secure,
        httponly=True,
    )

    return response
