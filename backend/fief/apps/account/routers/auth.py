from typing import cast

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from fastapi_users.manager import UserNotExists
from fastapi_users.router.common import ErrorCode as FastAPIUsersErrorCode
from furl import furl
from pydantic import UUID4

from fief.auth.jwt import AssymetricJWTStrategy
from fief.dependencies.account_managers import get_authorization_code_manager
from fief.dependencies.auth import (
    get_assymetric_jwt_strategy,
    get_authorization_parameters,
    get_client_by_authorization_parameters,
    get_client_by_login_request_data,
    get_client_by_token_request,
    get_login_request_data,
    get_token_request_data,
)
from fief.dependencies.users import UserManager, get_user_manager
from fief.errors import ErrorCode
from fief.managers import AuthorizationCodeManager
from fief.models import AuthorizationCode, Client, Tenant
from fief.schemas.auth import (
    AuthorizationParameters,
    AuthorizeResponse,
    LoginRequest,
    LoginResponse,
    TokenRequest,
    TokenResponse,
)

router = APIRouter()


@router.get("/authorize", name="auth:authorize", response_model=AuthorizeResponse)
async def authorize(
    authorization_parameters: AuthorizationParameters = Depends(
        get_authorization_parameters
    ),
    client: Client = Depends(get_client_by_authorization_parameters),
) -> AuthorizeResponse:
    return AuthorizeResponse(parameters=authorization_parameters, tenant=client.tenant)


@router.post("/login", name="auth:login")
async def login(
    login_request: LoginRequest = Depends(get_login_request_data),
    client: Client = Depends(get_client_by_login_request_data),
    user_manager: UserManager = Depends(get_user_manager),
    authorization_code_manager: AuthorizationCodeManager = Depends(
        get_authorization_code_manager
    ),
):
    user = await user_manager.authenticate(
        cast(OAuth2PasswordRequestForm, login_request)
    )

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=FastAPIUsersErrorCode.LOGIN_BAD_CREDENTIALS,
        )
    # if requires_verification and not user.is_verified:
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail=ErrorCode.LOGIN_USER_NOT_VERIFIED,
    #     )

    authorization_code = await authorization_code_manager.create(
        AuthorizationCode(
            redirect_uri=login_request.redirect_uri,
            scope=login_request.scope,
            user_id=user.id,
            client_id=client.id,
        )
    )

    parsed_redirect_uri = furl(login_request.redirect_uri)
    parsed_redirect_uri.add(query_params={"code": authorization_code.code})
    if login_request.state is not None:
        parsed_redirect_uri.add(query_params={"state": login_request.state})

    return LoginResponse(redirect_uri=parsed_redirect_uri.url)


@router.post("/token", name="auth:token")
async def token(
    token_request: TokenRequest = Depends(get_token_request_data),
    user_manager: UserManager = Depends(get_user_manager),
    authorization_code_manager: AuthorizationCodeManager = Depends(
        get_authorization_code_manager
    ),
    assymetric_jwt_strategy: AssymetricJWTStrategy = Depends(
        get_assymetric_jwt_strategy
    ),
) -> TokenResponse:
    authorization_code = await authorization_code_manager.get_by_code(
        token_request.code
    )

    if authorization_code is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorCode.AUTH_INVALID_AUTHORIZATION_CODE,
        )

    client = authorization_code.client

    if (
        client.client_id != token_request.client_id
        or client.client_secret != token_request.client_secret
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorCode.AUTH_INVALID_CLIENT_ID_SECRET,
        )

    if authorization_code.redirect_uri != token_request.redirect_uri:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorCode.AUTH_REDIRECT_URI_MISMATCH,
        )

    user_id = cast(UUID4, authorization_code.user_id)

    try:
        user = await user_manager.get(user_id)
    except UserNotExists as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorCode.AUTH_INVALID_AUTHORIZATION_CODE,
        ) from e
    else:
        access_token = await assymetric_jwt_strategy.write_token(user)
        return TokenResponse(access_token=access_token)
    finally:
        await authorization_code_manager.delete(authorization_code)
