from typing import Optional

from fastapi import Header, HTTPException, status
from fastapi.param_functions import Depends
from pydantic import UUID4
from sqlalchemy import select

from fief.dependencies.account_managers import get_tenant_manager
from fief.managers import TenantManager
from fief.models.tenant import Tenant


async def get_current_tenant(
    tenant_id: Optional[UUID4] = Header(None, alias="x-fief-tenant"),
    manager: TenantManager = Depends(get_tenant_manager),
) -> Tenant:
    statement = select(Tenant)
    if tenant_id is None:
        statement = statement.where(Tenant.default == True)
    else:
        statement = statement.where(Tenant.id == tenant_id)
    tenant = await manager.get_one_or_none(statement)

    if tenant is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)

    return tenant
