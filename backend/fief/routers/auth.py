from fastapi import APIRouter, Depends

from fief.dependencies.auth import (
    get_authorization_parameters,
    get_tenant_by_authorization_parameters,
)
from fief.models import Tenant
from fief.schemas.auth import AuthorizationParameters, AuthorizeResponse

router = APIRouter()


@router.get("/authorize", name="auth:authorize", response_model=AuthorizeResponse)
async def authorize(
    authorization_parameters: AuthorizationParameters = Depends(
        get_authorization_parameters
    ),
    tenant: Tenant = Depends(get_tenant_by_authorization_parameters),
) -> AuthorizeResponse:
    return AuthorizeResponse(parameters=authorization_parameters, tenant=tenant)
