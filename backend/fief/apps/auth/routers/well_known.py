from fastapi import APIRouter
from fastapi.param_functions import Depends
from jwcrypto import jwk

from fief.dependencies.tenant import get_current_tenant
from fief.models import Tenant

router = APIRouter()


@router.get("/jwks.json", name="well_known:jwks")
async def get_jwks(tenant: Tenant = Depends(get_current_tenant)):
    keyset = jwk.JWKSet(keys=tenant.get_sign_jwk())
    return keyset.export(private_keys=False, as_dict=True)
