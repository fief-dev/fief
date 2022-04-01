from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import UUID4
from sqlalchemy import select

from fief.crypto.token import get_token_hash
from fief.dependencies.current_workspace import get_current_workspace
from fief.dependencies.main_managers import get_admin_api_key_manager
from fief.dependencies.pagination import (
    Ordering,
    PaginatedObjects,
    Pagination,
    get_ordering,
    get_paginated_objects,
    get_pagination,
)
from fief.managers import AdminAPIKeyManager
from fief.models import AdminAPIKey, Workspace

bearer_scheme = HTTPBearer(auto_error=False)


async def get_optional_admin_api_key(
    authorization: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    manager: AdminAPIKeyManager = Depends(get_admin_api_key_manager),
) -> Optional[AdminAPIKey]:
    if authorization is None:
        return None
    token_hash = get_token_hash(authorization.credentials)
    admin_api_key = await manager.get_by_token(token_hash)
    return admin_api_key


async def get_paginated_api_keys(
    pagination: Pagination = Depends(get_pagination),
    ordering: Ordering = Depends(get_ordering),
    manager: AdminAPIKeyManager = Depends(get_admin_api_key_manager),
    current_workspace: Workspace = Depends(get_current_workspace),
) -> PaginatedObjects[AdminAPIKey]:
    statement = select(AdminAPIKey).where(
        AdminAPIKey.workspace_id == current_workspace.id
    )
    return await get_paginated_objects(statement, pagination, ordering, manager)


async def get_api_key_by_id_or_404(
    id: UUID4,
    manager: AdminAPIKeyManager = Depends(get_admin_api_key_manager),
    current_workspace: Workspace = Depends(get_current_workspace),
) -> AdminAPIKey:
    statement = select(AdminAPIKey).where(
        AdminAPIKey.id == id,
        AdminAPIKey.workspace_id == current_workspace.id,
    )
    api_key = await manager.get_one_or_none(statement)

    if api_key is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    return api_key
