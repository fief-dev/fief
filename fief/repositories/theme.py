from sqlalchemy import select

from fief.models import Theme
from fief.repositories.base import BaseRepository, UUIDRepositoryMixin


class ThemeRepository(BaseRepository[Theme], UUIDRepositoryMixin[Theme]):
    model = Theme

    async def get_default(self) -> Theme | None:
        statement = select(Theme).where(Theme.default == True)
        return await self.get_one_or_none(statement)
