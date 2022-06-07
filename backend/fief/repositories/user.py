from sqlalchemy import select

from fief.models import User
from fief.repositories.base import BaseRepository, UUIDRepositoryMixin


class UserRepository(BaseRepository[User], UUIDRepositoryMixin[User]):
    model = User

    async def count_all(self) -> int:
        statement = select(User)
        return await self._count(statement)
