from datetime import datetime
from typing import AsyncGenerator, List, Optional, TypedDict

from fastapi import Depends, Form
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi_users.manager import UserNotExists
from pydantic import UUID4

from fief.dependencies.users import UserManager, get_user_manager
from fief.dependencies.workspace_managers import (
    get_authorization_code_manager,
    get_client_manager,
    get_refresh_token_manager,
)
from fief.exceptions import TokenRequestException
from fief.managers import AuthorizationCodeManager, ClientManager, RefreshTokenManager
from fief.models import Client
from fief.schemas.auth import TokenError
from fief.schemas.user import UserDB

ClientSecretBasicScheme = HTTPBasic(scheme_name="client_secret_basic", auto_error=False)


class GrantRequest(TypedDict):
    user_id: UUID4
    scope: List[str]
    authenticated_at: datetime
    nonce: Optional[str]
    client: Client


async def authenticate_client_secret_basic(
    credentials: Optional[HTTPBasicCredentials] = Depends(ClientSecretBasicScheme),
    client_manager: ClientManager = Depends(get_client_manager),
) -> Optional[Client]:
    if credentials is None:
        return None

    return await client_manager.get_by_client_id_and_secret(
        credentials.username, credentials.password
    )


async def authenticate_client_secret_post(
    client_id: Optional[str] = Form(None),
    client_secret: Optional[str] = Form(None),
    client_manager: ClientManager = Depends(get_client_manager),
) -> Optional[Client]:
    if client_id is None or client_secret is None:
        return None

    return await client_manager.get_by_client_id_and_secret(client_id, client_secret)


async def authenticate_client_secret(
    client_secret_basic: Optional[Client] = Depends(authenticate_client_secret_basic),
    client_secret_post: Optional[Client] = Depends(authenticate_client_secret_post),
) -> Client:
    if client_secret_basic is not None:
        return client_secret_basic

    if client_secret_post is not None:
        return client_secret_post

    raise TokenRequestException(TokenError.get_invalid_client())


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
    client: Client = Depends(authenticate_client_secret),
    authorization_code_manager: AuthorizationCodeManager = Depends(
        get_authorization_code_manager
    ),
    refresh_token_manager: RefreshTokenManager = Depends(get_refresh_token_manager),
) -> AsyncGenerator[GrantRequest, None]:
    if grant_type == "authorization_code":
        if code is None:
            raise TokenRequestException(TokenError.get_invalid_request())

        if redirect_uri is None:
            raise TokenRequestException(TokenError.get_invalid_request())

        authorization_code = await authorization_code_manager.get_valid_by_code(code)
        if authorization_code is None:
            raise TokenRequestException(TokenError.get_invalid_grant())

        if authorization_code.client.id != client.id:
            raise TokenRequestException(TokenError.get_invalid_grant())

        if authorization_code.redirect_uri != redirect_uri:
            raise TokenRequestException(TokenError.get_invalid_grant())

        yield {
            "user_id": authorization_code.user_id,
            "scope": authorization_code.scope,
            "authenticated_at": authorization_code.authenticated_at,
            "nonce": authorization_code.nonce,
            "client": client,
        }

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

        yield {
            "user_id": refresh_token.user_id,
            "scope": new_scope,
            "authenticated_at": refresh_token.authenticated_at,
            "nonce": None,
            "client": client,
        }

        await refresh_token_manager.delete(refresh_token)
        return

    raise TokenRequestException(TokenError.get_unsupported_grant_type())


async def get_user_from_grant_request(
    grant_request: GrantRequest = Depends(validate_grant_request),
    user_manager: UserManager = Depends(get_user_manager),
) -> UserDB:
    try:
        return await user_manager.get(grant_request["user_id"])
    except UserNotExists as e:
        raise TokenRequestException(TokenError.get_invalid_grant()) from e
