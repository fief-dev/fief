from fastapi import status
from fastapi.responses import RedirectResponse
from furl import furl

from fief.managers import AuthorizationCodeManager, LoginSessionManager
from fief.models import AuthorizationCode, LoginSession
from fief.schemas.user import UserDB
from fief.settings import settings


class AuthorizationCodeFlow:
    def __init__(
        self,
        authorization_code_manager: AuthorizationCodeManager,
        login_session_manager: LoginSessionManager,
    ) -> None:
        self.authorization_code_manager = authorization_code_manager
        self.login_session_manager = login_session_manager

    async def get_redirect(
        self, login_session: LoginSession, user: UserDB
    ) -> RedirectResponse:
        authorization_code = await self.authorization_code_manager.create(
            AuthorizationCode(
                redirect_uri=login_session.redirect_uri,
                scope=login_session.scope,
                user_id=user.id,
                client_id=login_session.client.id,
            )
        )

        parsed_redirect_uri = furl(login_session.redirect_uri)
        parsed_redirect_uri.add(query_params={"code": authorization_code.code})
        if login_session.state is not None:
            parsed_redirect_uri.add(query_params={"state": login_session.state})

        response = RedirectResponse(
            url=parsed_redirect_uri.url, status_code=status.HTTP_302_FOUND
        )

        response.delete_cookie(
            settings.login_session_cookie_name,
            domain=settings.login_session_cookie_domain,
        )
        await self.login_session_manager.delete(login_session)

        return response
