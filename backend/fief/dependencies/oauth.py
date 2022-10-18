from typing import List, Optional

from fastapi import Cookie, Depends, Query
from pydantic import UUID4

from fief.dependencies.oauth_provider import get_oauth_providers
from fief.dependencies.tenant import get_current_tenant
from fief.dependencies.workspace_repositories import get_workspace_repository
from fief.exceptions import OAuthException
from fief.locale import gettext_lazy as _
from fief.models import LoginSession, OAuthProvider, Tenant
from fief.repositories import (
    LoginSessionRepository,
    OAuthProviderRepository,
    TenantRepository,
)
from fief.schemas.oauth import OAuthError
from fief.settings import settings


async def get_tenant_by_query(
    tenant_id: UUID4 = Query(..., alias="tenant"),
    tenant_repository: TenantRepository = Depends(
        get_workspace_repository(TenantRepository)
    ),
) -> Tenant:
    tenant = await tenant_repository.get_by_id(tenant_id)

    if tenant is None:
        raise OAuthException(
            OAuthError.get_invalid_tenant(_("Unknown tenant")), fatal=True
        )

    return tenant


async def get_optional_login_session_with_tenant_query(
    token: Optional[str] = Cookie(None, alias=settings.login_session_cookie_name),
    login_session_repository: LoginSessionRepository = Depends(
        get_workspace_repository(LoginSessionRepository)
    ),
    tenant: Tenant = Depends(get_tenant_by_query),
) -> Optional[LoginSession]:
    if token is None:
        return None

    login_session = await login_session_repository.get_by_token(token)
    if login_session is None:
        return None

    if login_session.client.tenant_id != tenant.id:
        return None

    return login_session


async def get_login_session_with_tenant_query(
    login_session: Optional[LoginSession] = Depends(
        get_optional_login_session_with_tenant_query
    ),
    tenant: Tenant = Depends(get_tenant_by_query),
    oauth_providers: Optional[List[OAuthProvider]] = Depends(get_oauth_providers),
) -> LoginSession:
    if login_session is None:
        raise OAuthException(
            OAuthError.get_invalid_session(_("Invalid login session.")),
            oauth_providers=oauth_providers,
            tenant=tenant,
        )

    return login_session


async def get_oauth_provider(
    provider: UUID4 = Query(...),
    oauth_provider_repository: OAuthProviderRepository = Depends(
        get_workspace_repository(OAuthProviderRepository)
    ),
    oauth_providers: Optional[List[OAuthProvider]] = Depends(get_oauth_providers),
    tenant: Tenant = Depends(get_current_tenant),
) -> OAuthProvider:
    oauth_provider = await oauth_provider_repository.get_by_id(provider)
    if oauth_provider is None:
        raise OAuthException(
            OAuthError.get_invalid_provider(_("Unknown OAuth provider")),
            oauth_providers=oauth_providers,
            tenant=tenant,
        )

    return oauth_provider
