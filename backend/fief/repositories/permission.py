from typing import Optional

from sqlalchemy import select

from fief.models import Permission
from fief.repositories.base import BaseRepository, UUIDRepositoryMixin


class PermissionRepository(BaseRepository[Permission], UUIDRepositoryMixin[Permission]):
    model = Permission

    async def get_by_codename(self, codename: str) -> Optional[Permission]:
        statement = select(Permission).where(Permission.codename == codename)
        return await self.get_one_or_none(statement)
