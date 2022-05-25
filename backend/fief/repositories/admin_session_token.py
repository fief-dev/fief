from typing import Optional

from sqlalchemy import select

from fief.models import AdminSessionToken
from fief.repositories.base import BaseRepository, UUIDRepositoryMixin


class AdminSessionTokenRepository(
    BaseRepository[AdminSessionToken], UUIDRepositoryMixin[AdminSessionToken]
):
    model = AdminSessionToken

    async def get_by_token(self, token: str) -> Optional[AdminSessionToken]:
        statement = select(AdminSessionToken).where(AdminSessionToken.token == token)
        return await self.get_one_or_none(statement)
