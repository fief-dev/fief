from fastapi import Depends, HTTPException, Query, Request, status
from pydantic import UUID4
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from fief.dependencies.pagination import (
    GetPaginatedObjects,
    Ordering,
    OrderingGetter,
    PaginatedObjects,
    Pagination,
    get_paginated_objects_getter,
    get_pagination,
)
from fief.models import Tenant
from fief.repositories import TenantRepository


async def get_current_tenant(
    request: Request,
    repository: TenantRepository = Depends(TenantRepository),
) -> Tenant:
    tenant_slug = request.path_params.get("tenant_slug")
    if tenant_slug is None:
        tenant = await repository.get_default()
    else:
        tenant = await repository.get_by_slug(tenant_slug)

    if tenant is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)

    return tenant


async def get_paginated_tenants(
    query: str | None = Query(None),
    pagination: Pagination = Depends(get_pagination),
    ordering: Ordering = Depends(OrderingGetter()),
    repository: TenantRepository = Depends(TenantRepository),
    get_paginated_objects: GetPaginatedObjects[Tenant] = Depends(
        get_paginated_objects_getter
    ),
) -> PaginatedObjects[Tenant]:
    statement = select(Tenant)

    if query is not None:
        statement = statement.where(Tenant.name.ilike(f"%{query}%"))

    return await get_paginated_objects(statement, pagination, ordering, repository)


async def get_tenant_by_id_or_404(
    id: UUID4,
    repository: TenantRepository = Depends(TenantRepository),
) -> Tenant:
    tenant = await repository.get_by_id(
        id, (selectinload(Tenant.theme), selectinload(Tenant.email_domain))
    )

    if tenant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    return tenant


async def get_tenants(
    repository: TenantRepository = Depends(TenantRepository),
) -> list[Tenant]:
    return await repository.all()
