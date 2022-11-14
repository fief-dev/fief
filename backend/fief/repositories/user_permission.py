from typing import Optional

from pydantic import UUID4
from sqlalchemy import delete, select
from sqlalchemy.orm import joinedload
from sqlalchemy.sql import Select

from fief.models import UserPermission
from fief.repositories.base import BaseRepository, UUIDRepositoryMixin


class UserPermissionRepository(
    BaseRepository[UserPermission], UUIDRepositoryMixin[UserPermission]
):
    model = UserPermission

    def get_by_user_statement(
        self, user: UUID4, *, direct_only: bool = False
    ) -> Select:
        statement = (
            select(UserPermission)
            .where(UserPermission.user_id == user)
            .options(
                joinedload(UserPermission.permission),
                joinedload(UserPermission.from_role),
            )
        )

        if direct_only:
            statement = statement.where(UserPermission.from_role == None)

        return statement

    async def get_by_permission_and_user(
        self, user: UUID4, permission: UUID4, *, direct_only: bool = False
    ) -> Optional[UserPermission]:
        statement = select(UserPermission).where(
            UserPermission.user_id == user, UserPermission.permission_id == permission
        )

        if direct_only:
            statement = statement.where(UserPermission.from_role == None)

        return await self.get_one_or_none(statement)

    async def delete_by_user_and_role(self, user: UUID4, from_role: UUID4) -> None:
        statement = delete(UserPermission).where(
            UserPermission.user_id == user, UserPermission.from_role_id == from_role
        )
        await self._execute_statement(statement)

    async def delete_by_permission_and_role(
        self, permission: UUID4, from_role: UUID4
    ) -> None:
        statement = delete(UserPermission).where(
            UserPermission.permission_id == permission,
            UserPermission.from_role_id == from_role,
        )
        await self._execute_statement(statement)

    async def delete_by_role(self, from_role: UUID4) -> None:
        statement = delete(UserPermission).where(
            UserPermission.from_role_id == from_role
        )
        await self._execute_statement(statement)
