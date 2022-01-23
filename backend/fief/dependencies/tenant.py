from typing import Optional

from fastapi import Depends, HTTPException, Query, status
from sqlalchemy import select

from fief.dependencies.account_managers import get_tenant_manager
from fief.managers import TenantManager
from fief.models.tenant import Tenant


async def get_current_tenant(
    tenant_slug: Optional[str] = Query(None),
    manager: TenantManager = Depends(get_tenant_manager),
) -> Tenant:
    if tenant_slug is None:
        tenant = await manager.get_default()
    else:
        tenant = await manager.get_by_slug(tenant_slug)

    if tenant is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)

    return tenant
