from datetime import datetime
from typing import AsyncGenerator, List, Optional, TypedDict

from fastapi import Depends, Form
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi_users.exceptions import UserNotExists
from pydantic import UUID4

from fief.crypto.code_challenge import verify_code_verifier
from fief.crypto.token import get_token_hash
from fief.dependencies.users import UserManager, get_user_manager
from fief.dependencies.workspace_repositories import (
    get_authorization_code_repository,
    get_client_repository,
    get_refresh_token_repository,
)
from fief.exceptions import TokenRequestException
from fief.models import Client, ClientType, User
from fief.repositories import (
    AuthorizationCodeRepository,
    ClientRepository,
    RefreshTokenRepository,
)
from fief.schemas.auth import TokenError

ClientSecretBasicScheme = HTTPBasic(scheme_name="client_secret_basic", auto_error=False)


class GrantRequest(TypedDict):
    user_id: UUID4
    scope: List[str]
    authenticated_at: datetime
    nonce: Optional[str]
    c_hash: Optional[str]
    client: Client
    grant_type: str


async def get_grant_type(grant_type: Optional[str] = Form(None)) -> str:
    if grant_type is None:
        raise TokenRequestException(TokenError.get_invalid_request())

    return grant_type


async def authenticate_client_secret_basic(
    credentials: Optional[HTTPBasicCredentials] = Depends(ClientSecretBasicScheme),
    client_repository: ClientRepository = Depends(get_client_repository),
) -> Optional[Client]:
    if credentials is None:
        return None

    return await client_repository.get_by_client_id_and_secret(
        credentials.username, credentials.password
    )


async def authenticate_client_secret_post(
    client_id: Optional[str] = Form(None),
    client_secret: Optional[str] = Form(None),
    client_repository: ClientRepository = Depends(get_client_repository),
) -> Optional[Client]:
    if client_id is None or client_secret is None:
        return None

    return await client_repository.get_by_client_id_and_secret(client_id, client_secret)


async def authenticate_none(
    client_id: Optional[str] = Form(None),
    client_repository: ClientRepository = Depends(get_client_repository),
    grant_type: str = Depends(get_grant_type),
    code_verifier: Optional[str] = Form(None),
) -> Optional[Client]:
    if client_id is None:
        return None

    client = await client_repository.get_by_client_id(client_id)

    if (
        client is None
        or client.client_type != ClientType.PUBLIC
        # Enforce PKCE for authorization_code grant
        or (grant_type == "authorization_code" and code_verifier is None)
    ):
        return None

    return client


async def authenticate_client(
    client_secret_basic: Optional[Client] = Depends(authenticate_client_secret_basic),
    client_secret_post: Optional[Client] = Depends(authenticate_client_secret_post),
    client_none: Optional[Client] = Depends(authenticate_none),
) -> Client:
    if client_secret_basic is not None:
        return client_secret_basic

    if client_secret_post is not None:
        return client_secret_post

    if client_none is not None:
        return client_none

    raise TokenRequestException(TokenError.get_invalid_client())


async def validate_grant_request(
    code: Optional[str] = Form(None),
    code_verifier: Optional[str] = Form(None),
    redirect_uri: Optional[str] = Form(None),
    refresh_token_token: Optional[str] = Form(None, alias="refresh_token"),
    scope: Optional[str] = Form(None),
    grant_type: str = Depends(get_grant_type),
    client: Client = Depends(authenticate_client),
    authorization_code_repository: AuthorizationCodeRepository = Depends(
        get_authorization_code_repository
    ),
    refresh_token_repository: RefreshTokenRepository = Depends(
        get_refresh_token_repository
    ),
) -> AsyncGenerator[GrantRequest, None]:
    if grant_type == "authorization_code":
        if code is None:
            raise TokenRequestException(TokenError.get_invalid_request())

        if redirect_uri is None:
            raise TokenRequestException(TokenError.get_invalid_request())

        code_hash = get_token_hash(code)
        authorization_code = await authorization_code_repository.get_valid_by_code(
            code_hash
        )
        if authorization_code is None:
            raise TokenRequestException(TokenError.get_invalid_grant())

        if authorization_code.client.id != client.id:
            raise TokenRequestException(TokenError.get_invalid_grant())

        if authorization_code.redirect_uri != redirect_uri:
            raise TokenRequestException(TokenError.get_invalid_grant())

        code_challenge_tuple = authorization_code.get_code_challenge_tuple()
        if code_challenge_tuple is not None:
            if code_verifier is None or not verify_code_verifier(
                code_verifier, code_challenge_tuple[0], code_challenge_tuple[1]
            ):
                raise TokenRequestException(TokenError.get_invalid_grant())
        elif code_verifier is not None:
            raise TokenRequestException(TokenError.get_invalid_grant())

        yield {
            "user_id": authorization_code.user_id,
            "scope": authorization_code.scope,
            "authenticated_at": authorization_code.authenticated_at,
            "nonce": authorization_code.nonce,
            "c_hash": authorization_code.c_hash,
            "client": client,
            "grant_type": grant_type,
        }

        await authorization_code_repository.delete(authorization_code)
        return
    elif grant_type == "refresh_token":
        if refresh_token_token is None:
            raise TokenRequestException(TokenError.get_invalid_request())

        token_hash = get_token_hash(refresh_token_token)
        refresh_token = await refresh_token_repository.get_by_token(token_hash)

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
            "c_hash": None,
            "client": client,
            "grant_type": grant_type,
        }

        await refresh_token_repository.delete(refresh_token)
        return

    raise TokenRequestException(TokenError.get_unsupported_grant_type())


async def get_user_from_grant_request(
    grant_request: GrantRequest = Depends(validate_grant_request),
    user_manager: UserManager = Depends(get_user_manager),
) -> User:
    try:
        return await user_manager.get(grant_request["user_id"])
    except UserNotExists as e:
        raise TokenRequestException(TokenError.get_invalid_grant()) from e
