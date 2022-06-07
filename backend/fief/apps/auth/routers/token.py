from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Response

from fief.crypto.access_token import generate_access_token
from fief.crypto.id_token import generate_id_token
from fief.crypto.token import generate_token
from fief.dependencies.current_workspace import get_current_workspace
from fief.dependencies.permission import (
    UserPermissionsGetter,
    get_user_permissions_getter,
)
from fief.dependencies.tenant import get_current_tenant
from fief.dependencies.token import (
    GrantRequest,
    get_user_from_grant_request,
    validate_grant_request,
)
from fief.dependencies.workspace_repositories import get_refresh_token_repository
from fief.models import RefreshToken, Tenant, User, Workspace
from fief.repositories import RefreshTokenRepository
from fief.schemas.auth import TokenResponse
from fief.settings import settings

router = APIRouter()


@router.post("/token", name="auth:token")
async def token(
    response: Response,
    grant_request: GrantRequest = Depends(validate_grant_request),
    user: User = Depends(get_user_from_grant_request),
    get_user_permissions: UserPermissionsGetter = Depends(get_user_permissions_getter),
    refresh_token_repository: RefreshTokenRepository = Depends(
        get_refresh_token_repository
    ),
    workspace: Workspace = Depends(get_current_workspace),
    tenant: Tenant = Depends(get_current_tenant),
):
    scope = grant_request["scope"]
    authenticated_at = grant_request["authenticated_at"]
    nonce = grant_request["nonce"]
    c_hash = grant_request["c_hash"]
    client = grant_request["client"]
    permissions = await get_user_permissions(user)

    tenant_host = tenant.get_host(workspace.domain)
    access_token = generate_access_token(
        tenant.get_sign_jwk(),
        tenant_host,
        client,
        user,
        scope,
        permissions,
        settings.access_id_token_lifetime_seconds,
    )
    id_token = generate_id_token(
        tenant.get_sign_jwk(),
        tenant_host,
        client,
        authenticated_at,
        user,
        settings.access_id_token_lifetime_seconds,
        nonce=nonce,
        c_hash=c_hash,
        access_token=access_token,
        encryption_key=client.get_encrypt_jwk(),
    )
    token_response = TokenResponse(
        access_token=access_token,
        id_token=id_token,
        expires_in=settings.access_id_token_lifetime_seconds,
    )

    if "offline_access" in scope:
        expires_at = datetime.now(timezone.utc) + timedelta(
            seconds=settings.refresh_token_lifetime_seconds
        )
        token, token_hash = generate_token()
        refresh_token = RefreshToken(
            token=token_hash,
            expires_at=expires_at,
            scope=scope,
            user_id=user.id,
            client_id=client.id,
            authenticated_at=authenticated_at,
        )
        refresh_token = await refresh_token_repository.create(refresh_token)
        token_response.refresh_token = token

    response.headers["Cache-Control"] = "no-store"
    response.headers["Pragma"] = "no-cache"
    return token_response.dict(exclude_none=True)
