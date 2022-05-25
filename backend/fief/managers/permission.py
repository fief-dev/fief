from typing import Optional

from sqlalchemy import select

from fief.managers.base import BaseManager, UUIDManagerMixin
from fief.models import Permission


class PermissionManager(BaseManager[Permission], UUIDManagerMixin[Permission]):
    model = Permission

    async def get_by_codename(self, codename: str) -> Optional[Permission]:
        statement = select(Permission).where(Permission.codename == codename)
        return await self.get_one_or_none(statement)
