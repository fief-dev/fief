from sqlalchemy import select

from fief.models import RegistrationSession
from fief.repositories.base import BaseRepository, ExpiresAtMixin, UUIDRepositoryMixin


class RegistrationSessionRepository(
    BaseRepository[RegistrationSession],
    UUIDRepositoryMixin[RegistrationSession],
    ExpiresAtMixin[RegistrationSession],
):
    model = RegistrationSession

    async def get_by_token(
        self, token: str, *, fresh: bool = True
    ) -> RegistrationSession | None:
        statement = select(RegistrationSession).where(
            RegistrationSession.token == token
        )
        if fresh:
            statement = statement.where(RegistrationSession.is_expired.is_(False))
        return await self.get_one_or_none(statement)
