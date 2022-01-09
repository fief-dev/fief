from typing import cast

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from fastapi_users.router.common import ErrorCode
from furl import furl

from fief.dependencies.account_managers import get_authorization_code_manager
from fief.dependencies.auth import (
    get_authorization_parameters,
    get_login_request_data,
    get_tenant_by_authorization_parameters,
)
from fief.dependencies.users import UserManager, get_user_manager
from fief.managers import AuthorizationCodeManager
from fief.models import AuthorizationCode, Tenant
from fief.schemas.auth import (
    AuthorizationParameters,
    AuthorizeResponse,
    LoginRequest,
    LoginResponse,
)

router = APIRouter()


@router.get("/authorize", name="auth:authorize", response_model=AuthorizeResponse)
async def authorize(
    authorization_parameters: AuthorizationParameters = Depends(
        get_authorization_parameters
    ),
    tenant: Tenant = Depends(get_tenant_by_authorization_parameters),
) -> AuthorizeResponse:
    return AuthorizeResponse(parameters=authorization_parameters, tenant=tenant)


@router.post("/login", name="auth:login")
async def login(
    login_request: LoginRequest = Depends(get_login_request_data),
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
            detail=ErrorCode.LOGIN_BAD_CREDENTIALS,
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
        )
    )

    parsed_redirect_uri = furl(login_request.redirect_uri)
    parsed_redirect_uri.add(query_params={"code": authorization_code.code})
    if login_request.state is not None:
        parsed_redirect_uri.add(query_params={"state": login_request.state})

    return LoginResponse(redirect_uri=parsed_redirect_uri.url)
