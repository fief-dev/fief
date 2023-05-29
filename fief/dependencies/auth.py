from datetime import datetime, timezone
from typing import TypedDict

from fastapi import Cookie, Depends, Query, Request, Response

from fief.dependencies.authentication_flow import get_authentication_flow
from fief.dependencies.branding import get_show_branding
from fief.dependencies.session_token import get_session_token
from fief.dependencies.tenant import get_current_tenant
from fief.dependencies.theme import get_current_theme
from fief.dependencies.workspace_repositories import get_workspace_repository
from fief.exceptions import (
    AuthorizeException,
    AuthorizeRedirectException,
    LoginException,
)
from fief.locale import gettext_lazy as _
from fief.models import Client, LoginSession, SessionToken, Tenant, Theme
from fief.repositories import ClientRepository, GrantRepository, LoginSessionRepository
from fief.schemas.auth import AuthorizeError, AuthorizeRedirectError, LoginError
from fief.services.authentication_flow import AuthenticationFlow
from fief.services.response_type import (
    ALLOWED_RESPONSE_TYPES,
    DEFAULT_RESPONSE_MODE,
    NONCE_REQUIRED_RESPONSE_TYPES,
)
from fief.settings import settings


async def get_authorize_client(
    client_id: str | None = Query(None),
    tenant: Tenant = Depends(get_current_tenant),
    repository: ClientRepository = Depends(get_workspace_repository(ClientRepository)),
) -> Client:
    if client_id is None:
        raise AuthorizeException(
            AuthorizeError.get_invalid_client(_("client_id is missing"))
        )

    client = await repository.get_by_client_id_and_tenant(client_id, tenant.id)

    if client is None:
        raise AuthorizeException(AuthorizeError.get_invalid_client(_("Unknown client")))

    return client


async def get_authorize_redirect_uri(
    redirect_uri: str | None = Query(None),
    client: Client = Depends(get_authorize_client),
) -> str:
    if redirect_uri is None:
        raise AuthorizeException(
            AuthorizeError.get_invalid_redirect_uri(_("redirect_uri is missing"))
        )

    if redirect_uri not in client.redirect_uris:
        raise AuthorizeException(
            AuthorizeError.get_invalid_redirect_uri(
                _("redirect_uri is not authorized for this client")
            )
        )

    return redirect_uri


async def get_authorize_state(state: str | None = Query(None)) -> str | None:
    return state


async def get_authorize_response_type(
    response_type: str | None = Query(None),
    redirect_uri: str = Depends(get_authorize_redirect_uri),
    state: str | None = Depends(get_authorize_state),
) -> str:
    if response_type is None:
        raise AuthorizeRedirectException(
            AuthorizeRedirectError.get_invalid_request(_("response_type is missing")),
            redirect_uri,
            "query",
            state,
        )

    if response_type not in ALLOWED_RESPONSE_TYPES:
        raise AuthorizeRedirectException(
            AuthorizeRedirectError.get_invalid_request(_("response_type is invalid")),
            redirect_uri,
            "query",
            state,
        )

    return response_type


async def get_authorize_response_mode(
    response_type: str = Depends(get_authorize_response_type),
) -> str:
    return DEFAULT_RESPONSE_MODE[response_type]


async def check_unsupported_request_parameter(
    request_parameter: str | None = Query(None, alias="request"),
    redirect_uri: str = Depends(get_authorize_redirect_uri),
    response_mode: str = Depends(get_authorize_response_mode),
    state: str | None = Depends(get_authorize_state),
) -> None:
    if request_parameter is not None:
        raise AuthorizeRedirectException(
            AuthorizeRedirectError.get_request_not_supported(
                _("request parameter is not supported")
            ),
            redirect_uri,
            response_mode,
            state,
        )


async def get_nonce(
    nonce: str | None = Query(None),
    response_type: str = Depends(get_authorize_response_type),
    redirect_uri: str = Depends(get_authorize_redirect_uri),
    response_mode: str = Depends(get_authorize_response_mode),
    state: str | None = Depends(get_authorize_state),
) -> str | None:
    if nonce is None and response_type in NONCE_REQUIRED_RESPONSE_TYPES:
        raise AuthorizeRedirectException(
            AuthorizeRedirectError.get_invalid_request(
                _("nonce parameter is required for this response_type")
            ),
            redirect_uri,
            response_mode,
            state,
        )

    return nonce


async def get_authorize_scope(
    scope: str | None = Query(None),
    redirect_uri: str = Depends(get_authorize_redirect_uri),
    response_mode: str = Depends(get_authorize_response_mode),
    state: str | None = Depends(get_authorize_state),
) -> list[str]:
    if scope is None:
        raise AuthorizeRedirectException(
            AuthorizeRedirectError.get_invalid_request(_("scope is missing")),
            redirect_uri,
            response_mode,
            state,
        )

    scope_list = scope.split()

    if "openid" not in scope_list:
        raise AuthorizeRedirectException(
            AuthorizeRedirectError.get_invalid_scope(
                _('scope should contain "openid"')
            ),
            redirect_uri,
            response_mode,
            state,
        )

    return scope_list


async def get_authorize_prompt(
    prompt: str | None = Query(None),
    session_token: SessionToken | None = Depends(get_session_token),
    redirect_uri: str = Depends(get_authorize_redirect_uri),
    response_mode: str = Depends(get_authorize_response_mode),
    state: str | None = Depends(get_authorize_state),
) -> str | None:
    if prompt is not None and prompt not in ["none", "login", "consent"]:
        raise AuthorizeRedirectException(
            AuthorizeRedirectError.get_invalid_request(
                _('prompt should either be "none", "login" or "register"')
            ),
            redirect_uri,
            response_mode,
            state,
        )

    if prompt in ["none", "consent"] and session_token is None:
        raise AuthorizeRedirectException(
            AuthorizeRedirectError.get_login_required(_("User is not logged in")),
            redirect_uri,
            response_mode,
            state,
        )

    return prompt


async def get_authorize_screen(
    screen: str = Query("login"),
    redirect_uri: str = Depends(get_authorize_redirect_uri),
    response_mode: str = Depends(get_authorize_response_mode),
    state: str | None = Depends(get_authorize_state),
) -> str:
    if screen not in ["login", "register"]:
        raise AuthorizeRedirectException(
            AuthorizeRedirectError.get_invalid_request(
                _('screen should either be "login" or "register"')
            ),
            redirect_uri,
            response_mode,
            state,
        )

    return screen


async def get_authorize_code_challenge(
    code_challenge: str | None = Query(None),
    code_challenge_method: str | None = Query("plain"),
    redirect_uri: str = Depends(get_authorize_redirect_uri),
    response_mode: str = Depends(get_authorize_response_mode),
    state: str | None = Depends(get_authorize_state),
) -> tuple[str, str] | None:
    if code_challenge is None:
        return None

    if code_challenge_method not in ["plain", "S256"]:
        raise AuthorizeRedirectException(
            AuthorizeRedirectError.get_invalid_request(
                _("Unsupported code_challenge_method")
            ),
            redirect_uri,
            response_mode,
            state,
        )

    return code_challenge, code_challenge_method


async def has_valid_session_token(
    max_age: int | None = Query(None),
    session_token: SessionToken | None = Depends(get_session_token),
) -> bool:
    if session_token is None:
        return False

    if max_age is not None:
        session_age = (
            datetime.now(timezone.utc) - session_token.created_at
        ).total_seconds()
        return session_age < max_age

    return True


async def get_optional_login_session(
    token: str | None = Cookie(None, alias=settings.login_session_cookie_name),
    login_session_repository: LoginSessionRepository = Depends(
        get_workspace_repository(LoginSessionRepository)
    ),
    tenant: Tenant = Depends(get_current_tenant),
) -> LoginSession | None:
    if token is None:
        return None

    login_session = await login_session_repository.get_by_token(token)
    if login_session is None or login_session.client.tenant_id != tenant.id:
        raise LoginException(
            LoginError.get_invalid_session(_("Invalid login session")), fatal=True
        )

    return login_session


async def get_login_session(
    login_session: LoginSession | None = Depends(get_optional_login_session),
    tenant: Tenant = Depends(get_current_tenant),
) -> LoginSession:
    if login_session is None:
        raise LoginException(
            LoginError.get_missing_session(
                _(
                    "Missing login session. You should return to %(tenant)s and try to login again",
                    tenant=tenant.name,
                )
            ),
            fatal=True,
        )

    return login_session


async def get_needs_consent(
    login_session: LoginSession = Depends(get_login_session),
    session_token: SessionToken | None = Depends(get_session_token),
    grant_repository: GrantRepository = Depends(
        get_workspace_repository(GrantRepository)
    ),
) -> bool:
    if session_token is None:
        return True

    client = login_session.client

    if client.first_party:
        return False

    client_id = client.id
    user_id = session_token.user_id
    grant = await grant_repository.get_by_user_and_client(user_id, client_id)

    if grant is None or not set(login_session.scope).issubset(set(grant.scope)):
        return True

    return False


async def get_consent_prompt(
    login_session: LoginSession = Depends(get_login_session),
    needs_consent: bool = Depends(get_needs_consent),
    tenant: Tenant = Depends(get_current_tenant),
    authentication_flow: AuthenticationFlow = Depends(get_authentication_flow),
) -> str | None:
    prompt = login_session.prompt
    if needs_consent and prompt == "none":
        await authentication_flow.delete_login_session(Response(), login_session)
        raise AuthorizeRedirectException(
            AuthorizeRedirectError.get_consent_required(
                _("User consent is required for this scope")
            ),
            login_session.redirect_uri,
            login_session.response_mode,
            login_session.state,
            tenant,
        )

    return prompt


class BaseContext(TypedDict):
    request: Request
    tenant: Tenant
    theme: Theme
    show_branding: bool


async def get_base_context(
    request: Request,
    tenant: Tenant = Depends(get_current_tenant),
    theme: Theme = Depends(get_current_theme),
    show_branding: bool = Depends(get_show_branding),
) -> BaseContext:
    return {
        "request": request,
        "tenant": tenant,
        "theme": theme,
        "show_branding": show_branding,
    }
