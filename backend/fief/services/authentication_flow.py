from datetime import datetime, timedelta, timezone
from typing import List, Optional, TypeVar

from fastapi import Response, status
from fastapi.responses import RedirectResponse
from furl import furl
from pydantic import UUID4

from fief.managers import (
    AuthorizationCodeManager,
    GrantManager,
    LoginSessionManager,
    SessionTokenManager,
)
from fief.models import AuthorizationCode, Client, Grant, LoginSession, SessionToken
from fief.settings import settings

ResponseType = TypeVar("ResponseType", bound=Response)


class AuthenticationFlow:
    def __init__(
        self,
        authorization_code_manager: AuthorizationCodeManager,
        login_session_manager: LoginSessionManager,
        session_token_manager: SessionTokenManager,
        grant_manager: GrantManager,
    ) -> None:
        self.authorization_code_manager = authorization_code_manager
        self.login_session_manager = login_session_manager
        self.session_token_manager = session_token_manager
        self.grant_manager = grant_manager

    async def create_login_session(
        self,
        response: ResponseType,
        *,
        response_type: str,
        redirect_uri: str,
        scope: List[str],
        state: Optional[str],
        nonce: Optional[str],
        client: Client,
    ) -> ResponseType:
        login_session = LoginSession(
            response_type=response_type,
            redirect_uri=redirect_uri,
            scope=scope,
            state=state,
            nonce=nonce,
            client_id=client.id,
        )
        login_session = await self.login_session_manager.create(login_session)

        response.set_cookie(
            settings.login_session_cookie_name,
            login_session.token,
            domain=settings.login_session_cookie_domain,
            secure=settings.login_session_cookie_secure,
        )

        return response

    async def delete_login_session(
        self, response: ResponseType, login_session: LoginSession
    ) -> ResponseType:
        response.delete_cookie(
            settings.login_session_cookie_name,
            domain=settings.login_session_cookie_domain,
        )
        await self.login_session_manager.delete(login_session)
        return response

    async def create_session_token(
        self, response: ResponseType, user_id: UUID4
    ) -> ResponseType:
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

    async def create_or_update_grant(
        self, user_id: UUID4, client: Client, scope: List[str]
    ) -> Grant:
        grant = await self.grant_manager.get_by_user_and_client(user_id, client.id)
        if grant is not None:
            grant.scope = scope
            await self.grant_manager.update(grant)
        else:
            grant = await self.grant_manager.create(
                Grant(scope=scope, user_id=user_id, client=client)
            )
        return grant

    async def get_authorization_code_success_redirect(
        self,
        redirect_uri: str,
        scope: List[str],
        authenticated_at: datetime,
        state: Optional[str],
        nonce: Optional[str],
        client: Client,
        user_id: UUID4,
    ) -> RedirectResponse:
        authorization_code = await self.authorization_code_manager.create(
            AuthorizationCode(
                redirect_uri=redirect_uri,
                scope=scope,
                authenticated_at=authenticated_at,
                nonce=nonce,
                user_id=user_id,
                client_id=client.id,
            )
        )

        parsed_redirect_uri = furl(redirect_uri)
        parsed_redirect_uri.add(query_params={"code": authorization_code.code})
        if state is not None:
            parsed_redirect_uri.add(query_params={"state": state})

        return RedirectResponse(
            url=parsed_redirect_uri.url, status_code=status.HTTP_302_FOUND
        )

    @classmethod
    def get_authorization_code_error_redirect(
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
