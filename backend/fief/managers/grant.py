from typing import Optional

from pydantic import UUID4
from sqlalchemy import select

from fief.managers.base import BaseManager, UUIDManagerMixin
from fief.models import Grant


class GrantManager(BaseManager[Grant], UUIDManagerMixin[Grant]):
    model = Grant

    async def get_by_user_and_client(
        self, user_id: UUID4, client_id: UUID4
    ) -> Optional[Grant]:
        statement = select(Grant).where(
            Grant.user_id == user_id, Grant.client_id == client_id
        )
        return await self.get_one_or_none(statement)
