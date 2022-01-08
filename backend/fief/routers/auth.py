from fastapi import Depends

from fief.dependencies.tenant import get_tenant_by_client_id
from fief.fastapi_users import bearer_token_backend, fastapi_users
from fief.models import Tenant
from fief.schemas.tenant import TenantReadPublic

router = fastapi_users.get_auth_router(bearer_token_backend)


@router.get("/authorize", response_model=TenantReadPublic)
async def authorize(
    tenant: Tenant = Depends(get_tenant_by_client_id),
) -> TenantReadPublic:
    return TenantReadPublic.from_orm(tenant)
