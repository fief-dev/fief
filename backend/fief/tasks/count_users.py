import uuid

import dramatiq
from sqlalchemy.exc import DBAPIError

from fief.logger import logger
from fief.repositories import UserRepository, WorkspaceRepository
from fief.tasks.base import TaskBase


class CountUsersWorkspaceTask(TaskBase):
    __name__ = "count_users_workspace"

    async def run(self, workspace_id: str):
        async with self.get_main_session() as session:
            workspace_repository = WorkspaceRepository(session)
            workspace = await self._get_workspace(uuid.UUID(workspace_id))
            try:
                async with self.get_workspace_session(workspace) as workspace_session:
                    user_repository = UserRepository(workspace_session)
                    workspace.users_count = await user_repository.count_all()
                    await workspace_repository.update(workspace)
            except ConnectionError:
                logger.warning(
                    "Could not connect to workspace", workspace_id=str(workspace.id)
                )
            except DBAPIError as e:
                logger.warning(
                    "An error occured while querying workspace",
                    workspace_id=str(workspace.id),
                    message=str(e),
                )


count_users_workspace = dramatiq.actor(CountUsersWorkspaceTask(), max_retries=0)


class CountUsersTask(TaskBase):
    __name__ = "count_users"

    async def run(self):
        async with self.get_main_session() as session:
            workspace_repository = WorkspaceRepository(session)
            workspaces = await workspace_repository.all()
            for workspace in workspaces:
                self.send_task(count_users_workspace, workspace_id=str(workspace.id))


count_users = dramatiq.actor(CountUsersTask())
