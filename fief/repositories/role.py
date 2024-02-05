from sqlalchemy import select

from fief.models import Role
from fief.repositories.base import BaseRepository, UUIDRepositoryMixin


class RoleRepository(BaseRepository[Role], UUIDRepositoryMixin[Role]):
    model = Role

    async def get_granted_by_default(self) -> list[Role]:
        statement = select(Role).where(Role.granted_by_default == True)
        return await self.list(statement)

    async def get_by_name(self, name: str) -> Role | None:
        statement = select(Role).where(Role.name == name)
        return await self.get_one_or_none(statement)
