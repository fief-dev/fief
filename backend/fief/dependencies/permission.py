from collections.abc import Callable, Coroutine
from typing import Any

from fastapi import Depends, HTTPException, Query, status
from pydantic import UUID4
from sqlalchemy import select

from fief.dependencies.pagination import (
    GetPaginatedObjects,
    Ordering,
    PaginatedObjects,
    Pagination,
    get_ordering,
    get_paginated_objects_getter,
    get_pagination,
)
from fief.dependencies.workspace_repositories import get_workspace_repository
from fief.models import Permission, User
from fief.repositories import PermissionRepository


async def get_paginated_permissions(
    query: str | None = Query(None),
    pagination: Pagination = Depends(get_pagination),
    ordering: Ordering = Depends(get_ordering),
    repository: PermissionRepository = Depends(
        get_workspace_repository(PermissionRepository)
    ),
    get_paginated_objects: GetPaginatedObjects[Permission] = Depends(
        get_paginated_objects_getter
    ),
) -> PaginatedObjects[Permission]:
    statement = select(Permission)

    if query is not None:
        statement = statement.where(
            Permission.name.ilike(f"%{query}%")
            | Permission.codename.ilike(f"%{query}%")
        )

    return await get_paginated_objects(statement, pagination, ordering, repository)


async def get_permission_by_id_or_404(
    id: UUID4,
    repository: PermissionRepository = Depends(
        get_workspace_repository(PermissionRepository)
    ),
) -> Permission:
    permission = await repository.get_by_id(id)

    if permission is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    return permission


UserPermissionsGetter = Callable[[User], Coroutine[Any, Any, list[str]]]


async def get_user_permissions_getter(
    repository: PermissionRepository = Depends(
        get_workspace_repository(PermissionRepository)
    ),
) -> UserPermissionsGetter:
    async def _get_user_permissions(user: User) -> list[str]:
        permissions = await repository.list(
            repository.get_user_permissions_statement(user.id)
        )
        return [permission.codename for permission in permissions]

    return _get_user_permissions
