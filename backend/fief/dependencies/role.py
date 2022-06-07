from typing import List, Optional, Tuple

from fastapi import Depends, HTTPException, Query, status
from pydantic import UUID4
from sqlalchemy import select

from fief.dependencies.pagination import (
    Ordering,
    Pagination,
    get_ordering,
    get_paginated_objects,
    get_pagination,
)
from fief.dependencies.workspace_repositories import get_role_repository
from fief.models import Role
from fief.repositories import RoleRepository


async def get_paginated_roles(
    query: Optional[str] = Query(None),
    pagination: Pagination = Depends(get_pagination),
    ordering: Ordering = Depends(get_ordering),
    repository: RoleRepository = Depends(get_role_repository),
) -> Tuple[List[Role], int]:
    statement = select(Role)

    if query is not None:
        statement = statement.where(Role.name.ilike(f"%{query}%"))

    return await get_paginated_objects(statement, pagination, ordering, repository)


async def get_role_by_id_or_404(
    id: UUID4,
    repository: RoleRepository = Depends(get_role_repository),
) -> Role:
    role = await repository.get_by_id(id)

    if role is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    return role
