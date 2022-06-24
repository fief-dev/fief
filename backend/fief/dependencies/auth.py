from datetime import datetime, timezone
from typing import List, Optional, Tuple

from fastapi import Cookie, Depends, Query, Response

from fief.dependencies.authentication_flow import get_authentication_flow
from fief.dependencies.session_token import get_session_token
from fief.dependencies.tenant import get_current_tenant
from fief.dependencies.workspace_repositories import (
    get_client_repository,
    get_grant_repository,
    get_login_session_repository,
)
from fief.exceptions import (
    AuthorizeException,
    AuthorizeRedirectException,
    LoginException,
)
from fief.locale import gettext_lazy as _
from fief.models import Client, LoginSession, SessionToken, Tenant
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
    client_id: Optional[str] = Query(None),
    repository: ClientRepository = Depends(get_client_repository),
) -> Client:
    if client_id is None:
        raise AuthorizeException(
            AuthorizeError.get_invalid_client(_("client_id is missing"))
        )

    client = await repository.get_by_client_id(client_id)

    if client is None:
        raise AuthorizeException(AuthorizeError.get_invalid_client(_("Unknown client")))

    return client


async def get_authorize_redirect_uri(
    redirect_uri: Optional[str] = Query(None),
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


async def get_authorize_state(state: Optional[str] = Query(None)) -> Optional[str]:
    return state


async def get_authorize_response_type(
    response_type: Optional[str] = Query(None),
    redirect_uri: str = Depends(get_authorize_redirect_uri),
    state: Optional[str] = Depends(get_authorize_state),
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
    request_parameter: Optional[str] = Query(None, alias="request"),
    redirect_uri: str = Depends(get_authorize_redirect_uri),
    response_mode: str = Depends(get_authorize_response_mode),
    state: Optional[str] = Depends(get_authorize_state),
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
    nonce: Optional[str] = Query(None),
    response_type: str = Depends(get_authorize_response_type),
    redirect_uri: str = Depends(get_authorize_redirect_uri),
    response_mode: str = Depends(get_authorize_response_mode),
    state: Optional[str] = Depends(get_authorize_state),
) -> Optional[str]:
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
    scope: Optional[str] = Query(None),
    redirect_uri: str = Depends(get_authorize_redirect_uri),
    response_mode: str = Depends(get_authorize_response_mode),
    state: Optional[str] = Depends(get_authorize_state),
) -> List[str]:
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
    prompt: Optional[str] = Query(None),
    session_token: Optional[SessionToken] = Depends(get_session_token),
    redirect_uri: str = Depends(get_authorize_redirect_uri),
    response_mode: str = Depends(get_authorize_response_mode),
    state: Optional[str] = Depends(get_authorize_state),
) -> Optional[str]:
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
    state: Optional[str] = Depends(get_authorize_state),
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
    code_challenge: Optional[str] = Query(None),
    code_challenge_method: Optional[str] = Query("plain"),
    redirect_uri: str = Depends(get_authorize_redirect_uri),
    response_mode: str = Depends(get_authorize_response_mode),
    state: Optional[str] = Depends(get_authorize_state),
) -> Optional[Tuple[str, str]]:
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
    max_age: Optional[int] = Query(None),
    session_token: Optional[SessionToken] = Depends(get_session_token),
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
    token: Optional[str] = Cookie(None, alias=settings.login_session_cookie_name),
    login_session_repository: LoginSessionRepository = Depends(
        get_login_session_repository
    ),
    tenant: Tenant = Depends(get_current_tenant),
) -> Optional[LoginSession]:
    if token is None:
        return None

    login_session = await login_session_repository.get_by_token(token)
    if login_session is None:
        return None

    if login_session.client.tenant_id != tenant.id:
        return None

    return login_session


async def get_login_session(
    login_session: Optional[LoginSession] = Depends(get_optional_login_session),
) -> LoginSession:
    if login_session is None:
        raise LoginException(
            LoginError.get_invalid_session(_("Invalid login session")), fatal=True
        )

    return login_session


async def get_needs_consent(
    login_session: LoginSession = Depends(get_login_session),
    session_token: Optional[SessionToken] = Depends(get_session_token),
    grant_repository: GrantRepository = Depends(get_grant_repository),
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
) -> Optional[str]:
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
