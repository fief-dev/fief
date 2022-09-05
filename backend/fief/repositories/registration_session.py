from datetime import datetime, timezone
from typing import Optional

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
    ) -> Optional[RegistrationSession]:
        statement = select(RegistrationSession).where(
            RegistrationSession.token == token
        )
        if fresh:
            statement = statement.where(
                RegistrationSession.expires_at > datetime.now(timezone.utc)
            )
        return await self.get_one_or_none(statement)
