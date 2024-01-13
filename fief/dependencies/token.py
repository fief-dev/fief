from collections.abc import AsyncGenerator
from datetime import datetime
from typing import TypedDict

from fastapi import Depends, Form
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import UUID4

from fief.crypto.code_challenge import verify_code_verifier
from fief.crypto.token import get_token_hash
from fief.dependencies.repositories import get_repository
from fief.dependencies.users import get_user_manager
from fief.exceptions import TokenRequestException
from fief.models import Client, ClientType, User
from fief.repositories import (
    AuthorizationCodeRepository,
    ClientRepository,
    RefreshTokenRepository,
)
from fief.schemas.auth import TokenError
from fief.services.acr import ACR
from fief.services.user_manager import UserDoesNotExistError, UserManager

ClientSecretBasicScheme = HTTPBasic(scheme_name="client_secret_basic", auto_error=False)


class GrantRequest(TypedDict):
    user_id: UUID4
    scope: list[str]
    authenticated_at: datetime
    acr: ACR
    nonce: str | None
    c_hash: str | None
    client: Client
    grant_type: str


async def get_grant_type(grant_type: str | None = Form(None)) -> str:
    if grant_type is None:
        raise TokenRequestException(TokenError.get_invalid_request())

    return grant_type


async def authenticate_client_secret_basic(
    credentials: HTTPBasicCredentials | None = Depends(ClientSecretBasicScheme),
    client_repository: ClientRepository = Depends(ClientRepository),
) -> Client | None:
    if credentials is None:
        return None

    return await client_repository.get_by_client_id_and_secret(
        credentials.username, credentials.password
    )


async def authenticate_client_secret_post(
    client_id: str | None = Form(None),
    client_secret: str | None = Form(None),
    client_repository: ClientRepository = Depends(ClientRepository),
) -> Client | None:
    if client_id is None or client_secret is None:
        return None

    return await client_repository.get_by_client_id_and_secret(client_id, client_secret)


async def authenticate_none(
    client_id: str | None = Form(None),
    client_repository: ClientRepository = Depends(ClientRepository),
    grant_type: str = Depends(get_grant_type),
    code_verifier: str | None = Form(None),
) -> Client | None:
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
    client_secret_basic: Client | None = Depends(authenticate_client_secret_basic),
    client_secret_post: Client | None = Depends(authenticate_client_secret_post),
    client_none: Client | None = Depends(authenticate_none),
) -> Client:
    if client_secret_basic is not None:
        return client_secret_basic

    if client_secret_post is not None:
        return client_secret_post

    if client_none is not None:
        return client_none

    raise TokenRequestException(TokenError.get_invalid_client())


async def validate_grant_request(
    code: str | None = Form(None),
    code_verifier: str | None = Form(None),
    redirect_uri: str | None = Form(None),
    refresh_token_token: str | None = Form(None, alias="refresh_token"),
    scope: str | None = Form(None),
    grant_type: str = Depends(get_grant_type),
    client: Client = Depends(authenticate_client),
    authorization_code_repository: AuthorizationCodeRepository = Depends(
        get_repository(AuthorizationCodeRepository)
    ),
    refresh_token_repository: RefreshTokenRepository = Depends(
        get_repository(RefreshTokenRepository)
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
            "acr": authorization_code.acr,
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
            "acr": ACR.LEVEL_ZERO,
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
        return await user_manager.get(
            grant_request["user_id"], grant_request["client"].tenant_id
        )
    except UserDoesNotExistError as e:
        raise TokenRequestException(TokenError.get_invalid_grant()) from e
