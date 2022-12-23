from dataclasses import dataclass

from fief.db.main import create_main_async_session_maker
from fief.db.workspace import WorkspaceEngineManager, get_workspace_session
from fief.models import Workspace
from fief.repositories import UserRepository, WorkspaceRepository


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
            try:
                async with get_workspace_session(
                    workspace, self.workspace_engine_manager
                ) as session:
                    user_repository = UserRepository(session)
                    nb_users = await user_repository.count_all()
                    stats.append(
                        WorkspaceStats(
                            workspace=workspace,
                            reachable=True,
                            external_db=workspace.database_type is not None,
                            nb_users=nb_users,
                        )
                    )
            except ConnectionError:
                stats.append(
                    WorkspaceStats(
                        workspace=workspace,
                        external_db=workspace.database_type is not None,
                        reachable=False,
                    )
                )

        return stats


async def get_workspaces_stats() -> list[WorkspaceStats]:
    main_async_session_maker = create_main_async_session_maker()
    workspace_engine_manager = WorkspaceEngineManager()
    async with main_async_session_maker() as session:
        workspace_repository = WorkspaceRepository(session)
        workspaces = Workspaces(workspace_repository, workspace_engine_manager)
        return await workspaces.get_stats()
