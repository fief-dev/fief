from fastapi import Depends
from sqlalchemy import select

from fief.dependencies.admin_session import get_admin_session_token
from fief.dependencies.main_repositories import get_workspace_repository
from fief.dependencies.pagination import (
    Ordering,
    PaginatedObjects,
    Pagination,
    get_ordering,
    get_paginated_objects,
    get_pagination,
)
from fief.models import AdminSessionToken, Workspace, WorkspaceUser
from fief.repositories import WorkspaceRepository


async def get_paginated_workspaces(
    pagination: Pagination = Depends(get_pagination),
    ordering: Ordering = Depends(get_ordering),
    repository: WorkspaceRepository = Depends(get_workspace_repository),
    admin_session_token: AdminSessionToken = Depends(get_admin_session_token),
) -> PaginatedObjects[Workspace]:
    statement = (
        select(Workspace)
        .join(Workspace.workspace_users)
        .where(WorkspaceUser.user_id == admin_session_token.user_id)
    )
    return await get_paginated_objects(statement, pagination, ordering, repository)
