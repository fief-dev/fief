from fastapi import Depends

from fief.dependencies.workspace_managers import (
    get_authorization_code_manager,
    get_grant_manager,
    get_login_session_manager,
    get_session_token_manager,
)
from fief.managers import (
    AuthorizationCodeManager,
    GrantManager,
    LoginSessionManager,
    SessionTokenManager,
)
from fief.services.authentication_flow import AuthenticationFlow


async def get_authentication_flow(
    authorization_code_manager: AuthorizationCodeManager = Depends(
        get_authorization_code_manager
    ),
    login_session_manager: LoginSessionManager = Depends(get_login_session_manager),
    session_token_manager: SessionTokenManager = Depends(get_session_token_manager),
    grant_manager: GrantManager = Depends(get_grant_manager),
) -> AuthenticationFlow:
    return AuthenticationFlow(
        authorization_code_manager,
        login_session_manager,
        session_token_manager,
        grant_manager,
    )
