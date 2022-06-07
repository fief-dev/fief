from typing import AsyncGenerator, Optional

from fastapi import Header, HTTPException, status
from fastapi.param_functions import Depends

from fief.db import AsyncSession
from fief.db.workspace import get_workspace_session
from fief.dependencies.main_repositories import get_workspace_repository
from fief.dependencies.workspace_db import get_workspace_db
from fief.errors import APIErrorCode
from fief.models import Workspace
from fief.repositories import WorkspaceRepository
from fief.services.workspace_db import WorkspaceDatabase


async def get_host(
    host: Optional[str] = Header(None, include_in_schema=False)
) -> Optional[str]:
    return host


async def get_current_workspace(
    host: Optional[str] = Depends(get_host),
    repository: WorkspaceRepository = Depends(get_workspace_repository),
    workspace_db: WorkspaceDatabase = Depends(get_workspace_db),
) -> Workspace:
    workspace = None
    if host is not None:
        workspace = await repository.get_by_domain(host)

    if workspace is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=APIErrorCode.CANT_DETERMINE_VALID_WORKSPACE,
        )

    latest_revision = workspace_db.get_latest_revision()
    if workspace.alembic_revision != latest_revision:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=APIErrorCode.WORKSPACE_DB_OUTDATED_MIGRATION,
        )

    return workspace


async def get_current_workspace_session(
    workspace: Workspace = Depends(get_current_workspace),
) -> AsyncGenerator[AsyncSession, None]:
    try:
        async with get_workspace_session(workspace) as session:
            yield session
    except ConnectionError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=APIErrorCode.WORKSPACE_DB_CONNECTION_ERROR,
        ) from e
