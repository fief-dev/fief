from datetime import datetime, timedelta, timezone
from typing import List, Optional

from fastapi import status
from fastapi.responses import RedirectResponse
from furl import furl
from pydantic import UUID4

from fief.managers import (
    AuthorizationCodeManager,
    LoginSessionManager,
    SessionTokenManager,
)
from fief.models import AuthorizationCode, Client, LoginSession, SessionToken
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
        self,
        redirect_uri: str,
        scope: List[str],
        state: Optional[str],
        client: Client,
        user_id: UUID4,
        *,
        login_session: Optional[LoginSession] = None,
        create_session: bool = True,
    ) -> RedirectResponse:
        authorization_code = await self.authorization_code_manager.create(
            AuthorizationCode(
                redirect_uri=redirect_uri,
                scope=scope,
                user_id=user_id,
                client_id=client.id,
            )
        )

        parsed_redirect_uri = furl(redirect_uri)
        parsed_redirect_uri.add(query_params={"code": authorization_code.code})
        if state is not None:
            parsed_redirect_uri.add(query_params={"state": state})

        response = RedirectResponse(
            url=parsed_redirect_uri.url, status_code=status.HTTP_302_FOUND
        )

        response.delete_cookie(
            settings.login_session_cookie_name,
            domain=settings.login_session_cookie_domain,
        )
        if login_session is not None:
            await self.login_session_manager.delete(login_session)

        if create_session:
            expires_at = datetime.now(timezone.utc) + timedelta(
                seconds=settings.session_lifetime_seconds
            )
            session_token = await self.session_token_manager.create(
                SessionToken(expires_at=expires_at, user_id=user_id)
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

    @classmethod
    def get_error_redirect(
        cls,
        redirect_uri: str,
        error: str,
        *,
        error_description: Optional[str] = None,
        error_uri: Optional[str] = None,
        state: Optional[str] = None,
    ) -> RedirectResponse:
        parsed_redirect_uri = furl(redirect_uri)

        query_params = {"error": error}
        if error_description is not None:
            query_params["error_description"] = error_description
        if error_uri is not None:
            query_params["error_uri"] = error_uri
        if state is not None:
            query_params["state"] = state
        parsed_redirect_uri.add(query_params=query_params)

        return RedirectResponse(
            url=parsed_redirect_uri.url, status_code=status.HTTP_302_FOUND
        )
