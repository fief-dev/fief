from fastapi import Depends, HTTPException, Query, status
from pydantic import UUID4
from sqlalchemy import select

from fief.dependencies.pagination import (
    GetPaginatedObjects,
    Ordering,
    OrderingGetter,
    PaginatedObjects,
    Pagination,
    get_paginated_objects_getter,
    get_pagination,
)
from fief.dependencies.tenant import get_current_tenant
from fief.dependencies.workspace_repositories import get_workspace_repository
from fief.models import Tenant, Theme
from fief.repositories import (
    OAuthProviderRepository,
    ThemeRepository,
    UserFieldRepository,
)
from fief.services.theme_preview import ThemePreview


async def get_paginated_themes(
    query: str | None = Query(None),
    pagination: Pagination = Depends(get_pagination),
    ordering: Ordering = Depends(OrderingGetter()),
    repository: ThemeRepository = Depends(get_workspace_repository(ThemeRepository)),
    get_paginated_objects: GetPaginatedObjects[Theme] = Depends(
        get_paginated_objects_getter
    ),
) -> PaginatedObjects[Theme]:
    statement = select(Theme)

    if query is not None:
        statement = statement.where(Theme.name.ilike(f"%{query}%"))

    return await get_paginated_objects(statement, pagination, ordering, repository)


async def get_theme_by_id_or_404(
    id: UUID4,
    repository: ThemeRepository = Depends(get_workspace_repository(ThemeRepository)),
) -> Theme:
    theme = await repository.get_by_id(id)

    if theme is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    return theme


async def get_theme_preview(
    oauth_provider_repository: OAuthProviderRepository = Depends(
        get_workspace_repository(OAuthProviderRepository)
    ),
    user_field_repository: UserFieldRepository = Depends(
        get_workspace_repository(UserFieldRepository)
    ),
) -> ThemePreview:
    return ThemePreview(oauth_provider_repository, user_field_repository)


async def get_current_theme(
    tenant: Tenant = Depends(get_current_tenant),
    repository: ThemeRepository = Depends(get_workspace_repository(ThemeRepository)),
) -> Theme:
    if tenant.theme_id is not None:
        theme = await repository.get_by_id(tenant.theme_id)
    else:
        theme = await repository.get_default()

    if theme is None:
        return Theme.build_default()

    return theme
