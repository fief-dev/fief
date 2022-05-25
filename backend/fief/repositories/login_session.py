from typing import Optional

from sqlalchemy import select

from fief.models import LoginSession
from fief.repositories.base import BaseRepository, UUIDRepositoryMixin


class LoginSessionRepository(
    BaseRepository[LoginSession], UUIDRepositoryMixin[LoginSession]
):
    model = LoginSession

    async def get_by_token(self, token: str) -> Optional[LoginSession]:
        statement = select(LoginSession).where(LoginSession.token == token)
        return await self.get_one_or_none(statement)
