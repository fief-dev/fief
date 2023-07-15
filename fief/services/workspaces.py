from dataclasses import dataclass

from fief.db.main import get_single_main_async_session
from fief.db.workspace import WorkspaceEngineManager
from fief.models import Workspace
from fief.repositories import WorkspaceRepository


@dataclass
class WorkspaceStats:
    workspace: Workspace
    reachable: bool
    external_db: bool
    nb_users: int | None = None


class Workspaces:
    def __init__(
        self,
        workspace_repository: WorkspaceRepository,
        workspace_engine_manager: WorkspaceEngineManager,
    ) -> None:
        self.workspace_repository = workspace_repository
        self.workspace_engine_manager = workspace_engine_manager

    async def get_stats(self) -> list[WorkspaceStats]:
        stats: list[WorkspaceStats] = []

        workspaces = await self.workspace_repository.all()
        for workspace in workspaces:
            stats.append(
                WorkspaceStats(
                    workspace=workspace,
                    reachable=True,
                    external_db=workspace.database_type is not None,
                    nb_users=workspace.users_count,
                )
            )

        return stats


async def get_workspaces_stats() -> list[WorkspaceStats]:
    async with get_single_main_async_session() as session:
        workspace_repository = WorkspaceRepository(session)
        async with WorkspaceEngineManager() as workspace_engine_manager:
            workspaces = Workspaces(workspace_repository, workspace_engine_manager)
            return await workspaces.get_stats()
