from fastapi import Depends
from posthog import Posthog

from fief.db.workspace import WorkspaceEngineManager
from fief.dependencies.db import get_workspace_engine_manager
from fief.dependencies.main_repositories import get_main_repository
from fief.dependencies.telemetry import get_posthog
from fief.dependencies.workspace_db import get_workspace_db
from fief.repositories import WorkspaceRepository, WorkspaceUserRepository
from fief.services.workspace_db import WorkspaceDatabase
from fief.services.workspace_manager import WorkspaceManager


async def get_workspace_manager(
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
    posthog: Posthog = Depends(get_posthog),
) -> WorkspaceManager:
    return WorkspaceManager(
        workspace_repository,
        workspace_user_repository,
        workspace_db,
        workspace_engine_manager,
        posthog,
    )
