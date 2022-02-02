from datetime import datetime, timedelta, timezone

from fastapi import status
from fastapi.responses import RedirectResponse
from furl import furl

from fief.managers import (
    AuthorizationCodeManager,
    LoginSessionManager,
    SessionTokenManager,
)
from fief.models import AuthorizationCode, LoginSession, SessionToken
from fief.schemas.user import UserDB
from fief.settings import settings


class AuthorizationCodeFlow:
    def __init__(
        self,
        authorization_code_manager: AuthorizationCodeManager,
        login_session_manager: LoginSessionManager,
        session_token_manager: SessionTokenManager,
    ) -> None:
        self.authorization_code_manager = authorization_code_manager
        self.login_session_manager = login_session_manager
        self.session_token_manager = session_token_manager

    async def get_success_redirect(
        self, login_session: LoginSession, user: UserDB, *, create_session: bool = True
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

        if create_session:
            expires_at = datetime.now(timezone.utc) + timedelta(
                seconds=settings.session_lifetime_seconds
            )
            session_token = await self.session_token_manager.create(
                SessionToken(expires_at=expires_at, user_id=user.id)
            )
            response.set_cookie(
                settings.session_cookie_name,
                value=session_token.token,
                max_age=settings.session_lifetime_seconds,
                domain=settings.session_cookie_domain,
                secure=settings.session_cookie_secure,
                httponly=True,
                samesite="strict",
            )

        return response
