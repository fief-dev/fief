from dataclasses import dataclass
from typing import List, Optional

from fief.db.main import main_async_session_maker
from fief.db.workspace import get_workspace_session
from fief.models import Workspace
from fief.repositories import UserRepository, WorkspaceRepository


@dataclass
class WorkspaceStats:
    workspace: Workspace
    reachable: bool
    external_db: bool
    nb_users: Optional[int] = None


class Workspaces:
    def __init__(self, workspace_repository: WorkspaceRepository) -> None:
        self.workspace_repository = workspace_repository

    async def get_stats(self) -> List[WorkspaceStats]:
        stats: List[WorkspaceStats] = []

        workspaces = await self.workspace_repository.all()
        for workspace in workspaces:
            try:
                async with get_workspace_session(workspace) as session:
                    user_repository = UserRepository(session)
                    nb_users = await user_repository.count_all()
                    stats.append(
                        WorkspaceStats(
                            workspace=workspace,
                            reachable=True,
                            external_db=workspace.database_type != None,
                            nb_users=nb_users,
                        )
                    )
            except ConnectionError:
                stats.append(
                    WorkspaceStats(
                        workspace=workspace,
                        external_db=workspace.database_type != None,
                        reachable=False,
                    )
                )

        return stats


async def get_workspaces_stats() -> List[WorkspaceStats]:
    async with main_async_session_maker() as session:
        workspace_repository = WorkspaceRepository(session)
        workspaces = Workspaces(workspace_repository)
        return await workspaces.get_stats()
