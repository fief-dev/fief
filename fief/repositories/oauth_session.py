from sqlalchemy import select

from fief.models import OAuthSession
from fief.repositories.base import BaseRepository, ExpiresAtMixin, UUIDRepositoryMixin


class OAuthSessionRepository(
    BaseRepository[OAuthSession],
    UUIDRepositoryMixin[OAuthSession],
    ExpiresAtMixin[OAuthSession],
):
    model = OAuthSession

    async def get_by_token(
        self, token: str, *, fresh: bool = True
    ) -> OAuthSession | None:
        statement = select(OAuthSession).where(OAuthSession.token == token)
        if fresh:
            statement = statement.where(OAuthSession.is_expired.is_(False))
        return await self.get_one_or_none(statement)
