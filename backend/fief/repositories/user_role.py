from typing import List, Optional

from pydantic import UUID4
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from sqlalchemy.sql import Select

from fief.models import UserRole
from fief.repositories.base import BaseRepository, UUIDRepositoryMixin


class UserRoleRepository(BaseRepository[UserRole], UUIDRepositoryMixin[UserRole]):
    model = UserRole

    def get_by_user_statement(self, user: UUID4) -> Select:
        statement = (
            select(UserRole)
            .where(UserRole.user_id == user)
            .options(joinedload(UserRole.role))
        )

        return statement

    async def get_by_role_and_user(
        self, user: UUID4, role: UUID4
    ) -> Optional[UserRole]:
        return await self.get_one_or_none(
            select(UserRole).where(UserRole.user_id == user, UserRole.role_id == role)
        )

    async def get_by_role(self, role: UUID4) -> List[UserRole]:
        return await self.list(select(UserRole).where(UserRole.role_id == role))
