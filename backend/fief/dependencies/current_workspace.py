from typing import AsyncGenerator, Optional

from fastapi import Header, HTTPException, status
from fastapi.param_functions import Depends

from fief.db import AsyncSession
from fief.db.workspace import get_workspace_session
from fief.dependencies.main_managers import get_workspace_manager
from fief.errors import APIErrorCode
from fief.managers import WorkspaceManager
from fief.models import Workspace


async def get_host(
    host: Optional[str] = Header(None, include_in_schema=False)
) -> Optional[str]:
    if host is not None:
        return host.split(":")[0]  # Remove port
    return host


async def get_current_workspace(
    host: Optional[str] = Depends(get_host),
    manager: WorkspaceManager = Depends(get_workspace_manager),
) -> Workspace:
    workspace = None
    if host is not None:
        workspace = await manager.get_by_domain(host)

    if workspace is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=APIErrorCode.CANT_DETERMINE_VALID_WORKSPACE,
        )

    return workspace


async def get_current_workspace_session(
    workspace: Workspace = Depends(get_current_workspace),
) -> AsyncGenerator[AsyncSession, None]:
    async with get_workspace_session(workspace) as session:
        yield session
