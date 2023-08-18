from pydantic import UUID4
from sqlalchemy import select

from fief.models import WorkspaceUser
from fief.repositories.base import BaseRepository, UUIDRepositoryMixin


class WorkspaceUserRepository(
    BaseRepository[WorkspaceUser], UUIDRepositoryMixin[WorkspaceUser]
):
    model = WorkspaceUser

    async def get_by_workspace_and_user(
        self, workspace_id: UUID4, user_id: UUID4
    ) -> WorkspaceUser | None:
        statement = select(WorkspaceUser).where(
            WorkspaceUser.workspace_id == workspace_id, WorkspaceUser.user_id == user_id
        )
        return await self.get_one_or_none(statement)

    async def get_by_workspace(self, workspace_id: UUID4) -> list[WorkspaceUser]:
        statement = select(WorkspaceUser).where(
            WorkspaceUser.workspace_id == workspace_id
        )
        return await self.list(statement)
