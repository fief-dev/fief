from gettext import gettext as _
from typing import AsyncGenerator, List, Optional, Tuple, cast

from fastapi import Cookie, Depends, Form, Query, Response
from fastapi_users.manager import UserNotExists
from pydantic import UUID4

from fief.dependencies.account_managers import (
    get_authorization_code_manager,
    get_client_manager,
    get_grant_manager,
    get_login_session_manager,
    get_refresh_token_manager,
)
from fief.dependencies.authentication_flow import get_authentication_flow
from fief.dependencies.session_token import get_session_token
from fief.dependencies.tenant import get_current_tenant
from fief.dependencies.users import UserManager, get_user_manager
from fief.errors import (
    AuthorizeException,
    AuthorizeRedirectException,
    ConsentException,
    LoginException,
    TokenRequestException,
)
from fief.managers import (
    AuthorizationCodeManager,
    ClientManager,
    GrantManager,
    LoginSessionManager,
    RefreshTokenManager,
)
from fief.models import Client, LoginSession, SessionToken, Tenant
from fief.schemas.auth import (
    AuthorizeError,
    AuthorizeRedirectError,
    ConsentError,
    LoginError,
    TokenError,
)
from fief.schemas.user import UserDB
from fief.services.authentication_flow import AuthenticationFlow
from fief.settings import settings


async def get_authorize_client(
    client_id: Optional[str] = Query(None),
    manager: ClientManager = Depends(get_client_manager),
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


async def get_login_session(
    token: Optional[str] = Cookie(None, alias=settings.login_session_cookie_name),
    login_session_manager: LoginSessionManager = Depends(get_login_session_manager),
    tenant: Tenant = Depends(get_current_tenant),
) -> LoginSession:
    invalid_session_error = LoginError.get_invalid_session(_("Invalid login session"))
    if token is None:
        raise LoginException(invalid_session_error, fatal=True)

    login_session = await login_session_manager.get_by_token(token)
    if login_session is None:
        raise LoginException(invalid_session_error, fatal=True)

    if login_session.client.tenant_id != tenant.id:
        raise LoginException(invalid_session_error, fatal=True)

    return login_session


async def get_consent_action(
    action: Optional[str] = Form(None),
    login_session: LoginSession = Depends(get_login_session),
    tenant: Tenant = Depends(get_current_tenant),
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

    client_id = cast(UUID4, login_session.client.id)
    user_id = cast(UUID4, session_token.user_id)
    grant = await grant_manager.get_by_user_and_client(user_id, client_id)

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
            login_session.state,
            tenant,
        )

    return prompt


async def authenticate_client_secret_post(
    client_id: Optional[str] = Form(None),
    client_secret: Optional[str] = Form(None),
    client_manager: ClientManager = Depends(get_client_manager),
) -> Client:
    if client_id is None or client_secret is None:
        raise TokenRequestException(TokenError.get_invalid_client())

    client = await client_manager.get_by_client_id_and_secret(client_id, client_secret)

    if client is None:
        raise TokenRequestException(TokenError.get_invalid_client())

    return client


async def get_grant_type(grant_type: Optional[str] = Form(None)) -> str:
    if grant_type is None:
        raise TokenRequestException(TokenError.get_invalid_request())

    return grant_type


async def validate_grant_request(
    code: Optional[str] = Form(None),
    redirect_uri: Optional[str] = Form(None),
    refresh_token_token: Optional[str] = Form(None, alias="refresh_token"),
    scope: Optional[str] = Form(None),
    grant_type: str = Depends(get_grant_type),
    client: Client = Depends(authenticate_client_secret_post),
    authorization_code_manager: AuthorizationCodeManager = Depends(
        get_authorization_code_manager
    ),
    refresh_token_manager: RefreshTokenManager = Depends(get_refresh_token_manager),
) -> AsyncGenerator[Tuple[UUID4, List[str], Client], None]:
    if grant_type == "authorization_code":
        if code is None:
            raise TokenRequestException(TokenError.get_invalid_request())

        if redirect_uri is None:
            raise TokenRequestException(TokenError.get_invalid_request())

        authorization_code = await authorization_code_manager.get_by_code(code)
        if authorization_code is None:
            raise TokenRequestException(TokenError.get_invalid_grant())

        if authorization_code.client.id != client.id:
            raise TokenRequestException(TokenError.get_invalid_grant())

        if authorization_code.redirect_uri != redirect_uri:
            raise TokenRequestException(TokenError.get_invalid_grant())

        yield (
            cast(UUID4, authorization_code.user_id),
            authorization_code.scope,
            client,
        )

        await authorization_code_manager.delete(authorization_code)
        return
    elif grant_type == "refresh_token":
        if refresh_token_token is None:
            raise TokenRequestException(TokenError.get_invalid_request())

        refresh_token = await refresh_token_manager.get_by_token(refresh_token_token)

        if refresh_token is None:
            raise TokenRequestException(TokenError.get_invalid_grant())

        if refresh_token.client.id != client.id:
            raise TokenRequestException(TokenError.get_invalid_grant())

        new_scope = scope.split() if scope is not None else refresh_token.scope
        if not set(new_scope).issubset(set(refresh_token.scope)):
            raise TokenRequestException(TokenError.get_invalid_scope())

        yield (cast(UUID4, refresh_token.user_id), new_scope, client)

        await refresh_token_manager.delete(refresh_token)
        return

    raise TokenRequestException(TokenError.get_unsupported_grant_type())


async def get_user_from_grant_request(
    grant_request: Tuple[UUID4, List[str], Client] = Depends(validate_grant_request),
    user_manager: UserManager = Depends(get_user_manager),
) -> UserDB:
    user_id, _, _ = grant_request
    try:
        return await user_manager.get(user_id)
    except UserNotExists as e:
        raise TokenRequestException(TokenError.get_invalid_grant()) from e
