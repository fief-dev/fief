from datetime import datetime, timedelta, timezone
from typing import List, Tuple

from fastapi import APIRouter, Depends
from pydantic import UUID4

from fief.crypto.access_token import generate_access_token
from fief.crypto.id_token import generate_id_token
from fief.dependencies.account import get_current_account
from fief.dependencies.account_managers import get_refresh_token_manager
from fief.dependencies.tenant import get_current_tenant
from fief.dependencies.token import get_user_from_grant_request, validate_grant_request
from fief.managers import RefreshTokenManager
from fief.models import Account, Client, RefreshToken, Tenant
from fief.schemas.auth import TokenResponse
from fief.schemas.user import UserDB

TOKEN_LIFETIME = 3600
REFRESH_TOKEN_LIFETIME = 3600 * 24 * 30

router = APIRouter()


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
