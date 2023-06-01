from fastapi import Depends, HTTPException, Query, Request, status
from pydantic import UUID4
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from fief import schemas
from fief.dependencies.pagination import (
    GetPaginatedObjects,
    Ordering,
    OrderingGetter,
    PaginatedObjects,
    Pagination,
    get_paginated_objects_getter,
    get_pagination,
)
from fief.dependencies.workspace_repositories import get_workspace_repository
from fief.errors import APIErrorCode
from fief.models import Tenant
from fief.repositories import TenantRepository


async def get_current_tenant(
    request: Request,
    repository: TenantRepository = Depends(get_workspace_repository(TenantRepository)),
) -> Tenant:
    tenant_slug = request.path_params.get("tenant_slug")
    if tenant_slug is None:
        tenant = await repository.get_default()
    else:
        tenant = await repository.get_by_slug(tenant_slug)

    if tenant is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)

    return tenant


async def get_tenant_from_create_user_internal(
    user_create: schemas.user.UserCreateInternal,
    repository: TenantRepository = Depends(get_workspace_repository(TenantRepository)),
) -> Tenant:
    tenant = await repository.get_by_id(user_create.tenant_id)

    if tenant is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=APIErrorCode.USER_CREATE_UNKNOWN_TENANT,
        )

    return tenant


async def get_paginated_tenants(
    query: str | None = Query(None),
    pagination: Pagination = Depends(get_pagination),
    ordering: Ordering = Depends(OrderingGetter()),
    repository: TenantRepository = Depends(get_workspace_repository(TenantRepository)),
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
    repository: TenantRepository = Depends(get_workspace_repository(TenantRepository)),
) -> Tenant:
    tenant = await repository.get_by_id(
        id, (selectinload(Tenant.theme), selectinload(Tenant.email_domain))
    )

    if tenant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    return tenant


async def get_tenants(
    repository: TenantRepository = Depends(get_workspace_repository(TenantRepository)),
) -> list[Tenant]:
    return await repository.all()
