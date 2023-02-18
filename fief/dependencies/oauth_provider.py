from fastapi import Depends, HTTPException, Query, status
from pydantic import UUID4
from sqlalchemy import or_, select

from fief.dependencies.pagination import (
    GetPaginatedObjects,
    Ordering,
    PaginatedObjects,
    Pagination,
    get_ordering,
    get_paginated_objects_getter,
    get_pagination,
)
from fief.dependencies.tenant import get_current_tenant
from fief.dependencies.workspace_repositories import get_workspace_repository
from fief.models import OAuthProvider, Tenant
from fief.repositories import OAuthProviderRepository


async def get_paginated_oauth_providers(
    query: str | None = Query(None),
    pagination: Pagination = Depends(get_pagination),
    ordering: Ordering = Depends(get_ordering),
    repository: OAuthProviderRepository = Depends(
        get_workspace_repository(OAuthProviderRepository)
    ),
    get_paginated_objects: GetPaginatedObjects[OAuthProvider] = Depends(
        get_paginated_objects_getter
    ),
) -> PaginatedObjects[OAuthProvider]:
    statement = select(OAuthProvider)

    if query is not None:
        statement = statement.where(
            or_(
                OAuthProvider.name.ilike(f"%{query}%"),
                OAuthProvider.provider.ilike(f"%{query}%"),
            )
        )

    return await get_paginated_objects(statement, pagination, ordering, repository)


async def get_oauth_provider_by_id_or_404(
    id: UUID4,
    repository: OAuthProviderRepository = Depends(
        get_workspace_repository(OAuthProviderRepository)
    ),
) -> OAuthProvider:
    oauth_provider = await repository.get_by_id(id)

    if oauth_provider is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    return oauth_provider


async def get_oauth_providers(
    tenant: Tenant = Depends(get_current_tenant),
) -> list[OAuthProvider]:
    return tenant.oauth_providers
