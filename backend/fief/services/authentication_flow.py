from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple, TypeVar

from fastapi import Response, status
from fastapi.responses import RedirectResponse
from furl import furl
from pydantic import UUID4

from fief.crypto.access_token import generate_access_token
from fief.crypto.id_token import generate_id_token, get_validation_hash
from fief.crypto.token import generate_token
from fief.managers import (
    AuthorizationCodeManager,
    GrantManager,
    LoginSessionManager,
    SessionTokenManager,
)
from fief.models import (
    AuthorizationCode,
    Client,
    Grant,
    LoginSession,
    SessionToken,
    Tenant,
    User,
    Workspace,
)
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
        response_mode: str,
        redirect_uri: str,
        scope: List[str],
        state: Optional[str],
        nonce: Optional[str],
        code_challenge_tuple: Optional[Tuple[str, str]],
        client: Client,
    ) -> ResponseType:
        login_session = LoginSession(
            response_type=response_type,
            response_mode=response_mode,
            redirect_uri=redirect_uri,
            scope=scope,
            state=state,
            nonce=nonce,
            client_id=client.id,
        )
        if code_challenge_tuple is not None:
            code_challenge, code_challenge_method = code_challenge_tuple
            login_session.code_challenge = code_challenge
            login_session.code_challenge_method = code_challenge_method

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
        token, token_hash = generate_token()
        expires_at = datetime.now(timezone.utc) + timedelta(
            seconds=settings.session_lifetime_seconds
        )
        await self.session_token_manager.create(
            SessionToken(token=token_hash, expires_at=expires_at, user_id=user_id)
        )
        response.set_cookie(
            settings.session_cookie_name,
            value=token,
            max_age=settings.session_lifetime_seconds,
            domain=settings.session_cookie_domain,
            secure=settings.session_cookie_secure,
            httponly=True,
        )

        return response

    async def rotate_session_token(
        self,
        response: ResponseType,
        user_id: UUID4,
        *,
        session_token: Optional[SessionToken],
    ) -> ResponseType:
        if session_token is not None:
            await self.session_token_manager.delete(session_token)
        return await self.create_session_token(response, user_id)

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
        *,
        login_session: LoginSession,
        authenticated_at: datetime,
        user: User,
        client: Client,
        tenant: Tenant,
        workspace: Workspace,
    ) -> RedirectResponse:
        code, code_hash = generate_token()
        c_hash = get_validation_hash(code)
        authorization_code = await self.authorization_code_manager.create(
            AuthorizationCode(
                code=code_hash,
                c_hash=c_hash,
                redirect_uri=login_session.redirect_uri,
                scope=login_session.scope,
                authenticated_at=authenticated_at,
                nonce=login_session.nonce,
                user_id=user.id,
                client_id=client.id,
            )
        )

        code_challenge_tuple = login_session.get_code_challenge_tuple()
        if code_challenge_tuple is not None:
            code_challenge, code_challenge_method = code_challenge_tuple
            authorization_code.code_challenge = code_challenge
            authorization_code.code_challenge_method = code_challenge_method

        params = {"code": code}

        if login_session.state is not None:
            params["state"] = login_session.state

        tenant_host = tenant.get_host(workspace.domain)
        access_token: Optional[str] = None

        if login_session.response_type in ["code token", "code id_token token"]:
            access_token = generate_access_token(
                tenant.get_sign_jwk(),
                tenant_host,
                client,
                user,
                login_session.scope,
                settings.access_id_token_lifetime_seconds,
            )
            params["access_token"] = access_token
            params["token_type"] = "bearer"

        if login_session.response_type in ["code id_token", "code id_token token"]:
            id_token = generate_id_token(
                tenant.get_sign_jwk(),
                tenant_host,
                client,
                authenticated_at,
                user,
                settings.access_id_token_lifetime_seconds,
                nonce=login_session.nonce,
                c_hash=c_hash,
                access_token=access_token,
                encryption_key=client.get_encrypt_jwk(),
            )
            params["id_token"] = id_token

        parsed_redirect_uri = furl(login_session.redirect_uri)

        if login_session.response_mode == "query":
            parsed_redirect_uri.query.add(params)
        elif login_session.response_mode == "fragment":
            parsed_redirect_uri.fragment.add(args=params)

        return RedirectResponse(
            url=parsed_redirect_uri.url, status_code=status.HTTP_302_FOUND
        )

    @classmethod
    def get_authorization_code_error_redirect(
        cls,
        redirect_uri: str,
        response_mode: str,
        error: str,
        *,
        error_description: Optional[str] = None,
        error_uri: Optional[str] = None,
        state: Optional[str] = None,
    ) -> RedirectResponse:
        parsed_redirect_uri = furl(redirect_uri)

        params = {"error": error}
        if error_description is not None:
            params["error_description"] = error_description
        if error_uri is not None:
            params["error_uri"] = error_uri
        if state is not None:
            params["state"] = state

        if response_mode == "query":
            parsed_redirect_uri.query.add(params)
        elif response_mode == "fragment":
            parsed_redirect_uri.fragment.add(args=params)

        return RedirectResponse(
            url=parsed_redirect_uri.url, status_code=status.HTTP_302_FOUND
        )
