from fastapi import Depends

from fief.dependencies.main_managers import (
    get_workspace_manager,
    get_workspace_user_manager,
)
from fief.dependencies.workspace_db import get_workspace_db
from fief.managers import WorkspaceManager, WorkspaceUserManager
from fief.services.workspace_creation import WorkspaceCreation
from fief.services.workspace_db import WorkspaceDatabase


async def get_workspace_creation(
    workspace_manager: WorkspaceManager = Depends(get_workspace_manager),
    workspace_user_manager: WorkspaceUserManager = Depends(get_workspace_user_manager),
    workspace_db: WorkspaceDatabase = Depends(get_workspace_db),
) -> WorkspaceCreation:
    return WorkspaceCreation(workspace_manager, workspace_user_manager, workspace_db)
