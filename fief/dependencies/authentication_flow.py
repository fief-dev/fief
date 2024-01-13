from fastapi import Depends

from fief.dependencies.permission import (
    UserPermissionsGetter,
    get_user_permissions_getter,
)
from fief.dependencies.repositories import get_repository
from fief.repositories import (
    AuthorizationCodeRepository,
    GrantRepository,
    LoginSessionRepository,
    SessionTokenRepository,
)
from fief.services.authentication_flow import AuthenticationFlow


async def get_authentication_flow(
    authorization_code_repository: AuthorizationCodeRepository = Depends(
        get_repository(AuthorizationCodeRepository)
    ),
    login_session_repository: LoginSessionRepository = Depends(
        get_repository(LoginSessionRepository)
    ),
    session_token_repository: SessionTokenRepository = Depends(
        get_repository(SessionTokenRepository)
    ),
    grant_repository: GrantRepository = Depends(GrantRepository),
    get_user_permissions: UserPermissionsGetter = Depends(get_user_permissions_getter),
) -> AuthenticationFlow:
    return AuthenticationFlow(
        authorization_code_repository,
        login_session_repository,
        session_token_repository,
        grant_repository,
        get_user_permissions,
    )
