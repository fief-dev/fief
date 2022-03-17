from typing import Optional

from pydantic import UUID4
from sqlalchemy import select

from fief.managers.base import BaseManager, UUIDManagerMixin
from fief.models import WorkspaceUser


class WorkspaceUserManager(BaseManager[WorkspaceUser], UUIDManagerMixin[WorkspaceUser]):
    model = WorkspaceUser

    async def get_by_workspace_and_user(
        self, workspace_id: UUID4, user_id: UUID4
    ) -> Optional[WorkspaceUser]:
        statement = select(WorkspaceUser).where(
            WorkspaceUser.workspace_id == workspace_id, WorkspaceUser.user_id == user_id
        )
        return await self.get_one_or_none(statement)
