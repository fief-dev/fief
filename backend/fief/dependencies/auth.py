from typing import List, Optional, Tuple, cast

from fastapi import Depends, Form, HTTPException, Query, status
from fastapi_users.manager import UserNotExists
from pydantic import UUID4

from fief.dependencies.account_managers import (
    get_authorization_code_manager,
    get_client_manager,
)
from fief.dependencies.users import UserManager, get_user_manager
from fief.errors import ErrorCode, TokenRequestException
from fief.managers import AuthorizationCodeManager, ClientManager
from fief.models import Client
from fief.schemas.auth import AuthorizationParameters, LoginRequest, TokenErrorResponse
from fief.schemas.user import UserDB


async def get_authorization_parameters(
    response_type: str = Query(..., regex="code"),
    client_id: str = Query(...),
    redirect_uri: str = Query(...),
    scope: str = Query(...),
    state: Optional[str] = Query(None),
) -> AuthorizationParameters:
    return AuthorizationParameters(
        response_type=response_type,
        client_id=client_id,
        redirect_uri=redirect_uri,
        scope=scope,
        state=state,
    )


async def get_client_by_authorization_parameters(
    authorization_parameters: AuthorizationParameters = Depends(
        get_authorization_parameters
    ),
    manager: ClientManager = Depends(get_client_manager),
) -> Client:
    client = await manager.get_by_client_id(authorization_parameters.client_id)

    if client is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorCode.AUTH_INVALID_CLIENT_ID,
        )

    return client


async def get_login_request_data(
    username: str = Form(...),
    password: str = Form(...),
    response_type: str = Form(..., regex="code"),
    client_id: str = Form(...),
    redirect_uri: str = Form(...),
    scope: List[str] = Form(...),
    state: Optional[str] = Form(None),
) -> LoginRequest:
    return LoginRequest(
        username=username,
        password=password,
        response_type=response_type,
        client_id=client_id,
        redirect_uri=redirect_uri,
        scope=scope,
        state=state,
    )


async def get_client_by_login_request_data(
    login_request: LoginRequest = Depends(get_login_request_data),
    manager: ClientManager = Depends(get_client_manager),
) -> Client:
    client = await manager.get_by_client_id(login_request.client_id)

    if client is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorCode.AUTH_INVALID_CLIENT_ID,
        )

    return client


async def authenticate_client_secret_post(
    client_id: Optional[str] = Form(None),
    client_secret: Optional[str] = Form(None),
    client_manager: ClientManager = Depends(get_client_manager),
) -> Client:
    if client_id is None or client_secret is None:
        raise TokenRequestException(TokenErrorResponse.get_invalid_client())

    client = await client_manager.get_by_client_id_and_secret(client_id, client_secret)

    if client is None:
        raise TokenRequestException(TokenErrorResponse.get_invalid_client())

    return client


async def get_grant_type(grant_type: Optional[str] = Form(None)) -> str:
    if grant_type is None:
        raise TokenRequestException(TokenErrorResponse.get_invalid_request())

    if grant_type not in ["authorization_code", "refresh_token"]:
        raise TokenRequestException(TokenErrorResponse.get_unsupported_grant_type())

    return grant_type


async def validate_grant_request(
    code: Optional[str] = Form(None),
    redirect_uri: Optional[str] = Form(None),
    grant_type: str = Depends(get_grant_type),
    client: Client = Depends(authenticate_client_secret_post),
    authorization_code_manager: AuthorizationCodeManager = Depends(
        get_authorization_code_manager
    ),
) -> Tuple[UUID4, List[str], Client]:
    if code is None:
        raise TokenRequestException(TokenErrorResponse.get_invalid_request())

    if redirect_uri is None:
        raise TokenRequestException(TokenErrorResponse.get_invalid_request())

    authorization_code = await authorization_code_manager.get_by_code(code)
    if authorization_code is None:
        raise TokenRequestException(TokenErrorResponse.get_invalid_grant())

    if authorization_code.client.id != client.id:
        raise TokenRequestException(TokenErrorResponse.get_invalid_grant())

    if authorization_code.redirect_uri != redirect_uri:
        raise TokenRequestException(TokenErrorResponse.get_invalid_grant())

    return (
        cast(UUID4, authorization_code.user_id),
        authorization_code.scope,
        client,
    )


async def get_user_from_grant_request(
    grant_request: Tuple[UUID4, List[str], Client] = Depends(validate_grant_request),
    user_manager: UserManager = Depends(get_user_manager),
) -> UserDB:
    user_id, _, _ = grant_request
    try:
        return await user_manager.get(user_id)
    except UserNotExists as e:
        raise TokenRequestException(TokenErrorResponse.get_invalid_grant()) from e
