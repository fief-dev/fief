import secrets

from fastapi import APIRouter, Depends, status

from fief.crypto.jwk import generate_jwk
from fief.dependencies.account_managers import get_tenant_manager
from fief.dependencies.tenant import get_current_tenant
from fief.managers import TenantManager
from fief.models import Tenant

router = APIRouter()


@router.post("/", name="encryption_keys:create", status_code=status.HTTP_201_CREATED)
async def create_encryption_key(
    tenant: Tenant = Depends(get_current_tenant),
    manager: TenantManager = Depends(get_tenant_manager),
):
    key = generate_jwk(secrets.token_urlsafe(), "enc")
    tenant.encrypt_jwk = key.export_public()
    await manager.update(tenant)

    return key.export(as_dict=True)
