from sqlalchemy import select

from fief.models import RefreshToken
from fief.repositories.base import BaseRepository, ExpiresAtMixin, UUIDRepositoryMixin


class RefreshTokenRepository(
    BaseRepository[RefreshToken],
    UUIDRepositoryMixin[RefreshToken],
    ExpiresAtMixin[RefreshToken],
):
    model = RefreshToken

    async def get_by_token(
        self, token: str, *, fresh: bool = True
    ) -> RefreshToken | None:
        statement = select(RefreshToken).where(RefreshToken.token == token)
        if fresh:
            statement = statement.where(RefreshToken.is_expired.is_(False))

        return await self.get_one_or_none(statement)
