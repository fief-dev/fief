from typing import List, Optional

from fastapi import Depends, Form, HTTPException, Query, status

from fief.dependencies.account_managers import get_client_manager
from fief.errors import ErrorCode
from fief.managers import ClientManager
from fief.models import Client
from fief.schemas.auth import AuthorizationParameters, LoginRequest, TokenRequest


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


async def get_token_request_data(
    grant_type: str = Form(..., regex="authorization_code"),
    code: str = Form(...),
    redirect_uri: str = Form(...),
    client_id: str = Form(...),
    client_secret: str = Form(...),
) -> TokenRequest:
    return TokenRequest(
        grant_type=grant_type,
        code=code,
        redirect_uri=redirect_uri,
        client_id=client_id,
        client_secret=client_secret,
    )


async def get_client_by_token_request(
    token_request: TokenRequest = Depends(get_token_request_data),
    manager: ClientManager = Depends(get_client_manager),
) -> Client:
    client = await manager.get_by_client_id(token_request.client_id)

    if client is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorCode.AUTH_INVALID_CLIENT_ID,
        )

    return client
