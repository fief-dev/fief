from typing import Optional

from sqlalchemy import select

from fief.managers.base import BaseManager, UUIDManagerMixin
from fief.models import UserField


class UserFieldManager(BaseManager[UserField], UUIDManagerMixin[UserField]):
    model = UserField

    async def get_by_slug(self, slug: str) -> Optional[UserField]:
        statement = select(UserField).where(UserField.slug == slug)
        return await self.get_one_or_none(statement)
