from fastapi import Depends

from fief.dependencies.account_managers import (
    get_authorization_code_manager,
    get_login_session_manager,
    get_session_token_manager,
)
from fief.managers import (
    AuthorizationCodeManager,
    LoginSessionManager,
    SessionTokenManager,
)
from fief.services.authorization_code_flow import AuthorizationCodeFlow


async def get_authorization_code_flow(
    authorization_code_manager: AuthorizationCodeManager = Depends(
        get_authorization_code_manager
    ),
    login_session_manager: LoginSessionManager = Depends(get_login_session_manager),
    session_token_manager: SessionTokenManager = Depends(get_session_token_manager),
) -> AuthorizationCodeFlow:
    return AuthorizationCodeFlow(
        authorization_code_manager, login_session_manager, session_token_manager
    )
