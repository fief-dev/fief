from sqlalchemy import select

from fief.models import UserField
from fief.repositories.base import BaseRepository, UUIDRepositoryMixin


class UserFieldRepository(BaseRepository[UserField], UUIDRepositoryMixin[UserField]):
    model = UserField

    async def get_by_slug(self, slug: str) -> UserField | None:
        statement = select(UserField).where(UserField.slug == slug)
        return await self.get_one_or_none(statement)

    async def get_registration_fields(self) -> list[UserField]:
        statement = select(UserField)
        user_fields = await self.list(statement)
        return [
            user_field
            for user_field in user_fields
            if user_field.configuration["at_registration"]
        ]

    async def get_update_fields(self) -> list[UserField]:
        statement = select(UserField)
        user_fields = await self.list(statement)
        return [
            user_field
            for user_field in user_fields
            if user_field.configuration["at_update"]
        ]
