from sqlalchemy import select

from fief.models import LoginSession
from fief.repositories.base import BaseRepository, ExpiresAtMixin, UUIDRepositoryMixin


class LoginSessionRepository(
    BaseRepository[LoginSession],
    UUIDRepositoryMixin[LoginSession],
    ExpiresAtMixin[LoginSession],
):
    model = LoginSession

    async def get_by_token(
        self, token: str, *, fresh: bool = True
    ) -> LoginSession | None:
        statement = select(LoginSession).where(LoginSession.token == token)
        if fresh:
            statement = statement.where(LoginSession.is_expired.is_(False))
        return await self.get_one_or_none(statement)
