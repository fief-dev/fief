from fastapi import APIRouter, Depends

from fief import schemas
from fief.dependencies.fief import get_cookie_session_token
from fief.dependencies.pagination import PaginatedObjects
from fief.dependencies.tenant import get_paginated_tenants
from fief.models import Tenant
from fief.schemas.generics import PaginatedResults

router = APIRouter(dependencies=[Depends(get_cookie_session_token)])


@router.get("/")
async def list_tenants(
    paginated_tenants: PaginatedObjects[Tenant] = Depends(get_paginated_tenants),
) -> PaginatedResults[schemas.tenant.Tenant]:
    tenants, count = paginated_tenants
    return PaginatedResults(
        count=count,
        results=[schemas.tenant.Tenant.from_orm(tenant) for tenant in tenants],
    )
