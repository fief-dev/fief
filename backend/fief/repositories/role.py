from typing import List

from sqlalchemy import select

from fief.models import Role
from fief.repositories.base import BaseRepository, UUIDRepositoryMixin


class RoleRepository(BaseRepository[Role], UUIDRepositoryMixin[Role]):
    model = Role

    async def get_granted_by_default(self) -> List[Role]:
        statement = select(Role).where(Role.granted_by_default == True)
        return await self.list(statement)
