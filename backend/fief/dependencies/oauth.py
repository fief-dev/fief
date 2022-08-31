from typing import List, Optional

from fastapi import Depends, Query
from pydantic import UUID4

from fief.dependencies.oauth_provider import get_oauth_providers
from fief.dependencies.tenant import get_current_tenant
from fief.dependencies.workspace_repositories import get_oauth_provider_repository
from fief.exceptions import OAuthException
from fief.locale import gettext_lazy as _
from fief.models import OAuthProvider, Tenant
from fief.repositories import OAuthProviderRepository
from fief.schemas.oauth import OAuthError


async def get_oauth_provider(
    provider: UUID4 = Query(...),
    oauth_provider_repository: OAuthProviderRepository = Depends(
        get_oauth_provider_repository
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
