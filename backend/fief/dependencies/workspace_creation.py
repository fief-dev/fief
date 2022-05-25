from fastapi import Depends

from fief.dependencies.main_repositories import (
    get_workspace_repository,
    get_workspace_user_repository,
)
from fief.dependencies.workspace_db import get_workspace_db
from fief.repositories import WorkspaceRepository, WorkspaceUserRepository
from fief.services.workspace_creation import WorkspaceCreation
from fief.services.workspace_db import WorkspaceDatabase


async def get_workspace_creation(
    workspace_repository: WorkspaceRepository = Depends(get_workspace_repository),
    workspace_user_repository: WorkspaceUserRepository = Depends(
        get_workspace_user_repository
    ),
    workspace_db: WorkspaceDatabase = Depends(get_workspace_db),
) -> WorkspaceCreation:
    return WorkspaceCreation(
        workspace_repository, workspace_user_repository, workspace_db
    )
