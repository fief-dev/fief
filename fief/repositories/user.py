from pydantic import UUID4
from sqlalchemy import select

from fief.models import User
from fief.repositories.base import BaseRepository, UUIDRepositoryMixin


class UserRepository(BaseRepository[User], UUIDRepositoryMixin[User]):
    model = User

    async def get_one_by_tenant(self, tenant: UUID4) -> User | None:
        statement = (
            select(User)
            .where(User.tenant_id == tenant)
            .order_by(User.created_at)
            .limit(1)
        )
        return await self.get_one_or_none(statement)

    async def count_all(self) -> int:
        statement = select(User)
        return await self._count(statement)
