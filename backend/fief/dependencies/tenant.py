from typing import List, Optional, Tuple

from fastapi import Depends, HTTPException, Query, status
from sqlalchemy import select

from fief import schemas
from fief.dependencies.pagination import (
    Ordering,
    Pagination,
    get_ordering,
    get_paginated_objects,
    get_pagination,
)
from fief.dependencies.workspace_repositories import get_tenant_repository
from fief.errors import APIErrorCode
from fief.models import Tenant
from fief.repositories import TenantRepository


async def get_current_tenant(
    tenant_slug: Optional[str] = Query(None),
    repository: TenantRepository = Depends(get_tenant_repository),
) -> Tenant:
    if tenant_slug is None:
        tenant = await repository.get_default()
    else:
        tenant = await repository.get_by_slug(tenant_slug)

    if tenant is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)

    return tenant


async def get_tenant_from_create_user_internal(
    user_create: schemas.user.UserCreateInternal,
    repository: TenantRepository = Depends(get_tenant_repository),
) -> Tenant:
    tenant = await repository.get_by_id(user_create.tenant_id)

    if tenant is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=APIErrorCode.USER_CREATE_UNKNOWN_TENANT,
        )

    return tenant


async def get_paginated_tenants(
    query: Optional[str] = Query(None),
    pagination: Pagination = Depends(get_pagination),
    ordering: Ordering = Depends(get_ordering),
    repository: TenantRepository = Depends(get_tenant_repository),
) -> Tuple[List[Tenant], int]:
    statement = select(Tenant)

    if query is not None:
        statement = statement.where(Tenant.name.ilike(f"%{query}%"))

    return await get_paginated_objects(statement, pagination, ordering, repository)
