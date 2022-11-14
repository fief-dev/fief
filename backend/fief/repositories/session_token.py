from datetime import datetime, timezone

from sqlalchemy import select

from fief.models import SessionToken
from fief.repositories.base import BaseRepository, ExpiresAtMixin, UUIDRepositoryMixin


class SessionTokenRepository(
    BaseRepository[SessionToken],
    UUIDRepositoryMixin[SessionToken],
    ExpiresAtMixin[SessionToken],
):
    model = SessionToken

    async def get_by_token(
        self, token: str, *, fresh: bool = True
    ) -> SessionToken | None:
        statement = select(SessionToken).where(SessionToken.token == token)
        if fresh:
            statement = statement.where(
                SessionToken.expires_at > datetime.now(timezone.utc)
            )

        return await self.get_one_or_none(statement)
