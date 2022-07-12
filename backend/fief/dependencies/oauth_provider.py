from typing import List, Tuple

from fastapi import Depends, HTTPException, status
from pydantic import UUID4
from sqlalchemy import select

from fief.dependencies.pagination import (
    Ordering,
    Pagination,
    get_ordering,
    get_paginated_objects,
    get_pagination,
)
from fief.dependencies.workspace_repositories import get_oauth_provider_repository
from fief.models import OAuthProvider
from fief.repositories import OAuthProviderRepository


async def get_paginated_oauth_providers(
    pagination: Pagination = Depends(get_pagination),
    ordering: Ordering = Depends(get_ordering),
    repository: OAuthProviderRepository = Depends(get_oauth_provider_repository),
) -> Tuple[List[OAuthProvider], int]:
    statement = select(OAuthProvider)
    return await get_paginated_objects(statement, pagination, ordering, repository)


async def get_oauth_provider_by_id_or_404(
    id: UUID4,
    repository: OAuthProviderRepository = Depends(get_oauth_provider_repository),
) -> OAuthProvider:
    oauth_provider = await repository.get_by_id(id)

    if oauth_provider is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    return oauth_provider
