from fastapi import APIRouter, Depends, Response, status

from fief import schemas
from fief.crypto.token import generate_token
from fief.dependencies.admin_api_key import (
    get_api_key_by_id_or_404,
    get_paginated_api_keys,
)
from fief.dependencies.admin_session import get_admin_session_token
from fief.dependencies.current_workspace import get_current_workspace
from fief.dependencies.logger import get_audit_logger
from fief.dependencies.main_repositories import get_main_repository
from fief.dependencies.pagination import PaginatedObjects
from fief.logger import AuditLogger
from fief.models import AdminAPIKey, AuditLogMessage, Workspace
from fief.repositories import AdminAPIKeyRepository
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
    repository: AdminAPIKeyRepository = Depends(
        get_main_repository(AdminAPIKeyRepository)
    ),
    audit_logger: AuditLogger = Depends(get_audit_logger),
) -> schemas.admin_api_key.AdminAPIKeyCreateResponse:
    token, token_hash = generate_token()
    api_key = AdminAPIKey(
        **create_api_key.dict(), token=token_hash, workspace_id=current_workspace.id
    )
    api_key = await repository.create(api_key)
    audit_logger.log_object_write(AuditLogMessage.OBJECT_CREATED, api_key)

    api_key_response = schemas.admin_api_key.AdminAPIKeyCreateResponse.from_orm(api_key)
    api_key_response.token = token
    return api_key_response


@router.delete(
    "/{id:uuid}",
    name="api_keys:delete",
    dependencies=[Depends(get_admin_session_token)],
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def delete_api_key(
    api_key: AdminAPIKey = Depends(get_api_key_by_id_or_404),
    repository: AdminAPIKeyRepository = Depends(
        get_main_repository(AdminAPIKeyRepository)
    ),
    audit_logger: AuditLogger = Depends(get_audit_logger),
) -> None:
    await repository.delete(api_key)
    audit_logger.log_object_write(AuditLogMessage.OBJECT_DELETED, api_key)
    return None
