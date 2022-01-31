from datetime import datetime, timedelta, timezone
from typing import List, Tuple, cast

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from fastapi_users.router.common import ErrorCode as FastAPIUsersErrorCode
from furl import furl
from pydantic import UUID4

from fief.crypto.access_token import generate_access_token
from fief.crypto.id_token import generate_id_token
from fief.dependencies.account import get_current_account
from fief.dependencies.account_managers import (
    get_authorization_code_manager,
    get_refresh_token_manager,
)
from fief.dependencies.auth import (
    get_authorization_parameters,
    get_client_by_authorization_parameters,
    get_client_by_login_request_data,
    get_login_request_data,
    get_user_from_grant_request,
    validate_grant_request,
)
from fief.dependencies.tenant import get_current_tenant
from fief.dependencies.users import UserManager, get_user_manager
from fief.managers import AuthorizationCodeManager, RefreshTokenManager
from fief.models import Account, AuthorizationCode, Client, RefreshToken, Tenant
from fief.schemas.auth import (
    AuthorizationParameters,
    AuthorizeResponse,
    LoginRequest,
    LoginResponse,
    TokenResponse,
)
from fief.schemas.user import UserDB

router = APIRouter()

TOKEN_LIFETIME = 3600
REFRESH_TOKEN_LIFETIME = 3600 * 24 * 30


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
    grant_request: Tuple[UUID4, List[str], Client] = Depends(validate_grant_request),
    user: UserDB = Depends(get_user_from_grant_request),
    refresh_token_manager: RefreshTokenManager = Depends(get_refresh_token_manager),
    account: Account = Depends(get_current_account),
    tenant: Tenant = Depends(get_current_tenant),
):
    _, scope, client = grant_request

    tenant_host = tenant.get_host(account.domain)
    access_token = generate_access_token(
        tenant.get_sign_jwk(), tenant_host, client, user, scope, TOKEN_LIFETIME
    )
    id_token = generate_id_token(
        tenant.get_sign_jwk(),
        tenant_host,
        client,
        user,
        TOKEN_LIFETIME,
        encryption_key=tenant.get_encrypt_jwk(),
    )
    token_response = TokenResponse(
        access_token=access_token, id_token=id_token, expires_in=TOKEN_LIFETIME
    )

    if "offline_access" in scope:
        expires_at = datetime.now(timezone.utc) + timedelta(
            seconds=REFRESH_TOKEN_LIFETIME
        )
        refresh_token = RefreshToken(
            expires_at=expires_at, scope=scope, user_id=user.id, client_id=client.id
        )
        refresh_token = await refresh_token_manager.create(refresh_token)
        token_response.refresh_token = refresh_token.token

    return token_response.dict(exclude_none=True)
