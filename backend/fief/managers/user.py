from sqlalchemy import select

from fief.managers.base import BaseManager, UUIDManagerMixin
from fief.models import User


class UserManager(BaseManager[User], UUIDManagerMixin[User]):
    model = User

    async def count_all(self) -> int:
        statement = select(User)
        return await self._count(statement)
