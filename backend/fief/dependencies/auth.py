from typing import List, Optional

from fastapi import Depends, Form, HTTPException, Query, status

from fief.dependencies.account_managers import get_tenant_manager
from fief.errors import ErrorCode
from fief.managers import TenantManager
from fief.models.tenant import Tenant
from fief.schemas.auth import AuthorizationParameters, LoginRequest


async def get_authorization_parameters(
    response_type: str = Query(...),
    client_id: str = Query(...),
    redirect_uri: str = Query(...),
    scope: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
) -> AuthorizationParameters:
    return AuthorizationParameters(
        response_type=response_type,
        client_id=client_id,
        redirect_uri=redirect_uri,
        scope=scope,
        state=state,
    )


async def get_tenant_by_authorization_parameters(
    authorization_parameters: AuthorizationParameters = Depends(
        get_authorization_parameters
    ),
    manager: TenantManager = Depends(get_tenant_manager),
) -> Tenant:
    tenant = await manager.get_by_client_id(authorization_parameters.client_id)

    if tenant is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorCode.AUTH_INVALID_CLIENT_ID,
        )

    return tenant


async def get_login_request_data(
    username: str = Form(...),
    password: str = Form(...),
    response_type: str = Form(...),
    client_id: str = Form(...),
    redirect_uri: str = Form(...),
    scope: Optional[List[str]] = Form(None),
    state: Optional[str] = Form(None),
) -> LoginRequest:
    return LoginRequest(
        username=username,
        password=password,
        response_type=response_type,
        client_id=client_id,
        redirect_uri=redirect_uri,
        scope=scope,
        state=state,
    )
