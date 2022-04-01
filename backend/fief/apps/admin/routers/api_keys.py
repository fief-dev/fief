from fastapi import APIRouter, Depends, status

from fief import schemas
from fief.crypto.token import generate_token
from fief.dependencies.admin_api_key import (
    get_api_key_by_id_or_404,
    get_paginated_api_keys,
)
from fief.dependencies.admin_session import get_admin_session_token
from fief.dependencies.current_workspace import get_current_workspace
from fief.dependencies.main_managers import get_admin_api_key_manager
from fief.dependencies.pagination import PaginatedObjects
from fief.managers import AdminAPIKeyManager
from fief.models import AdminAPIKey, Workspace
from fief.schemas.generics import PaginatedResults

router = APIRouter()


@router.get("/", name="api_keys:list", dependencies=[Depends(get_admin_session_token)])
async def list_api_keys(
    paginated_api_keys: PaginatedObjects[AdminAPIKey] = Depends(get_paginated_api_keys),
) -> PaginatedResults[schemas.admin_api_key.AdminAPIKey]:
    api_keys, count = paginated_api_keys
    return PaginatedResults(
        count=count,
        results=[
            schemas.admin_api_key.AdminAPIKey.from_orm(api_key) for api_key in api_keys
        ],
    )


@router.post(
    "/",
    name="api_keys:create",
    dependencies=[Depends(get_admin_session_token)],
    status_code=status.HTTP_201_CREATED,
)
async def create_api_key(
    create_api_key: schemas.admin_api_key.AdminAPIKeyCreate,
    current_workspace: Workspace = Depends(get_current_workspace),
    manager: AdminAPIKeyManager = Depends(get_admin_api_key_manager),
) -> schemas.admin_api_key.AdminAPIKeyCreateResponse:
    token, token_hash = generate_token()
    api_key = AdminAPIKey(
        **create_api_key.dict(), token=token_hash, workspace_id=current_workspace.id
    )
    api_key = await manager.create(api_key)

    api_key_response = schemas.admin_api_key.AdminAPIKeyCreateResponse.from_orm(api_key)
    api_key_response.token = token
    return api_key_response


@router.delete(
    "/{id:uuid}",
    name="api_keys:delete",
    dependencies=[Depends(get_admin_session_token)],
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_api_key(
    api_key: AdminAPIKey = Depends(get_api_key_by_id_or_404),
    manager: AdminAPIKeyManager = Depends(get_admin_api_key_manager),
) -> None:
    await manager.delete(api_key)
    return None
