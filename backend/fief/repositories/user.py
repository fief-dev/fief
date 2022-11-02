from typing import Optional

from pydantic import UUID4
from sqlalchemy import select

from fief.models import User
from fief.repositories.base import BaseRepository, UUIDRepositoryMixin


class UserRepository(BaseRepository[User], UUIDRepositoryMixin[User]):
    model = User

    async def get_one_by_tenant(self, tenant: UUID4) -> Optional[User]:
        statement = select(User).where(User.tenant_id == tenant).limit(1)
        users = await self.list(statement)
        if len(users) == 0:
            return None
        return users[0]

    async def count_all(self) -> int:
        statement = select(User)
        return await self._count(statement)
