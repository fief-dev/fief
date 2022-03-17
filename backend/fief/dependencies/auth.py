from typing import List, Optional

from fastapi import Cookie, Depends, Form, Query, Response
from pydantic import UUID4

from fief.dependencies.authentication_flow import get_authentication_flow
from fief.dependencies.locale import get_gettext
from fief.dependencies.session_token import get_session_token
from fief.dependencies.tenant import get_current_tenant
from fief.dependencies.workspace_managers import (
    get_client_manager,
    get_grant_manager,
    get_login_session_manager,
)
from fief.exceptions import (
    AuthorizeException,
    AuthorizeRedirectException,
    ConsentException,
    LoginException,
)
from fief.managers import ClientManager, GrantManager, LoginSessionManager
from fief.models import Client, LoginSession, SessionToken, Tenant
from fief.schemas.auth import (
    AuthorizeError,
    AuthorizeRedirectError,
    ConsentError,
    LoginError,
)
from fief.services.authentication_flow import AuthenticationFlow
from fief.settings import settings


async def get_authorize_client(
    client_id: Optional[str] = Query(None),
    manager: ClientManager = Depends(get_client_manager),
    _=Depends(get_gettext),
) -> Client:
    if client_id is None:
        raise AuthorizeException(
            AuthorizeError.get_invalid_client(_("client_id is missing"))
        )

    client = await manager.get_by_client_id(client_id)

    if client is None:
        raise AuthorizeException(AuthorizeError.get_invalid_client(_("Unknown client")))

    return client


async def get_authorize_redirect_uri(
    redirect_uri: Optional[str] = Query(None),
    _=Depends(get_gettext),
) -> str:
    if redirect_uri is None:
        raise AuthorizeException(
            AuthorizeError.get_invalid_redirect_uri(_("redirect_uri is missing"))
        )

    return redirect_uri


async def get_authorize_state(state: Optional[str] = Query(None)) -> Optional[str]:
    return state


async def get_authorize_response_type(
    response_type: Optional[str] = Query(None),
    redirect_uri: str = Depends(get_authorize_redirect_uri),
    state: Optional[str] = Depends(get_authorize_state),
    _=Depends(get_gettext),
) -> str:
    if response_type is None:
        raise AuthorizeRedirectException(
            AuthorizeRedirectError.get_invalid_request(_("response_type is missing")),
            redirect_uri,
            state,
        )

    if response_type != "code":
        raise AuthorizeRedirectException(
            AuthorizeRedirectError.get_invalid_request(
                _('response_type should be "code"')
            ),
            redirect_uri,
            state,
        )

    return response_type


async def get_authorize_scope(
    scope: Optional[str] = Query(None),
    redirect_uri: str = Depends(get_authorize_redirect_uri),
    state: Optional[str] = Depends(get_authorize_state),
    _=Depends(get_gettext),
) -> List[str]:
    if scope is None:
        raise AuthorizeRedirectException(
            AuthorizeRedirectError.get_invalid_request(_("scope is missing")),
            redirect_uri,
            state,
        )

    scope_list = scope.split()

    if "openid" not in scope_list:
        raise AuthorizeRedirectException(
            AuthorizeRedirectError.get_invalid_scope(
                _('scope should contain "openid"')
            ),
            redirect_uri,
            state,
        )

    return scope_list


async def get_authorize_prompt(
    prompt: Optional[str] = Query(None),
    session_token: Optional[SessionToken] = Depends(get_session_token),
    redirect_uri: str = Depends(get_authorize_redirect_uri),
    state: Optional[str] = Depends(get_authorize_state),
    _=Depends(get_gettext),
) -> Optional[str]:
    if prompt is not None and prompt not in ["none", "login", "consent"]:
        raise AuthorizeRedirectException(
            AuthorizeRedirectError.get_invalid_request(
                _('prompt should either be "none", "login" or "register"')
            ),
            redirect_uri,
            state,
        )

    if prompt in ["none", "consent"] and session_token is None:
        raise AuthorizeRedirectException(
            AuthorizeRedirectError.get_login_required(_("User is not logged in")),
            redirect_uri,
            state,
        )

    return prompt


async def get_authorize_screen(
    screen: str = Query("login"),
    redirect_uri: str = Depends(get_authorize_redirect_uri),
    state: Optional[str] = Depends(get_authorize_state),
    _=Depends(get_gettext),
) -> str:
    if screen not in ["login", "register"]:
        raise AuthorizeRedirectException(
            AuthorizeRedirectError.get_invalid_request(
                _('screen should either be "login" or "register"')
            ),
            redirect_uri,
            state,
        )

    return screen


async def get_optional_login_session(
    token: Optional[str] = Cookie(None, alias=settings.login_session_cookie_name),
    login_session_manager: LoginSessionManager = Depends(get_login_session_manager),
    tenant: Tenant = Depends(get_current_tenant),
) -> Optional[LoginSession]:
    if token is None:
        return None

    login_session = await login_session_manager.get_by_token(token)
    if login_session is None:
        return None

    if login_session.client.tenant_id != tenant.id:
        return None

    return login_session


async def get_login_session(
    login_session: Optional[LoginSession] = Depends(get_optional_login_session),
    _=Depends(get_gettext),
) -> LoginSession:
    if login_session is None:
        raise LoginException(
            LoginError.get_invalid_session(_("Invalid login session")), fatal=True
        )

    return login_session


async def get_consent_action(
    action: Optional[str] = Form(None),
    login_session: LoginSession = Depends(get_login_session),
    tenant: Tenant = Depends(get_current_tenant),
    _=Depends(get_gettext),
) -> str:
    if action is None or action not in ["allow", "deny"]:
        raise ConsentException(
            ConsentError.get_invalid_action(
                _('action should either be "allow" or "deny"')
            ),
            login_session.client,
            login_session.scope,
            tenant,
        )

    return action


async def get_needs_consent(
    login_session: LoginSession = Depends(get_login_session),
    session_token: Optional[SessionToken] = Depends(get_session_token),
    grant_manager: GrantManager = Depends(get_grant_manager),
) -> bool:
    if session_token is None:
        return True

    client = login_session.client

    if client.first_party:
        return False

    client_id = client.id
    user_id = session_token.user_id
    grant = await grant_manager.get_by_user_and_client(user_id, client_id)

    if grant is None or not set(login_session.scope).issubset(set(grant.scope)):
        return True

    return False


async def get_consent_prompt(
    login_session: LoginSession = Depends(get_login_session),
    needs_consent: bool = Depends(get_needs_consent),
    tenant: Tenant = Depends(get_current_tenant),
    authentication_flow: AuthenticationFlow = Depends(get_authentication_flow),
    _=Depends(get_gettext),
) -> Optional[str]:
    prompt = login_session.prompt
    if needs_consent and prompt == "none":
        await authentication_flow.delete_login_session(Response(), login_session)
        raise AuthorizeRedirectException(
            AuthorizeRedirectError.get_consent_required(
                _("User consent is required for this scope")
            ),
            login_session.redirect_uri,
            login_session.state,
            tenant,
        )

    return prompt
