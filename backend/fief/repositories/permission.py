from typing import Optional

from pydantic import UUID4
from sqlalchemy import select
from sqlalchemy.sql import Select

from fief.models import Permission, UserPermission
from fief.repositories.base import BaseRepository, UUIDRepositoryMixin


class PermissionRepository(BaseRepository[Permission], UUIDRepositoryMixin[Permission]):
    model = Permission

    async def get_by_codename(self, codename: str) -> Optional[Permission]:
        statement = select(Permission).where(Permission.codename == codename)
        return await self.get_one_or_none(statement)

    def get_user_permissions_statement(self, user: UUID4) -> Select:
        statement = (
            select(Permission)
            .join(UserPermission, UserPermission.permission_id == Permission.id)
            .where(UserPermission.user_id == user)
        )

        return statement
