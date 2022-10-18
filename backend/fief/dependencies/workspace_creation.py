from fastapi import Depends

from fief.db.workspace import WorkspaceEngineManager
from fief.dependencies.db import get_workspace_engine_manager
from fief.dependencies.main_repositories import get_main_repository
from fief.dependencies.workspace_db import get_workspace_db
from fief.repositories import WorkspaceRepository, WorkspaceUserRepository
from fief.services.workspace_creation import WorkspaceCreation
from fief.services.workspace_db import WorkspaceDatabase


async def get_workspace_creation(
    workspace_repository: WorkspaceRepository = Depends(
        get_main_repository(WorkspaceRepository)
    ),
    workspace_user_repository: WorkspaceUserRepository = Depends(
        get_main_repository(WorkspaceUserRepository)
    ),
    workspace_db: WorkspaceDatabase = Depends(get_workspace_db),
    workspace_engine_manager: WorkspaceEngineManager = Depends(
        get_workspace_engine_manager
    ),
) -> WorkspaceCreation:
    return WorkspaceCreation(
        workspace_repository,
        workspace_user_repository,
        workspace_db,
        workspace_engine_manager,
    )
