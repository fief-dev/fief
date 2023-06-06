from datetime import datetime, timezone, timedelta

from sqlalchemy import select

from fief.models import AuthorizationCode
from fief.repositories.base import BaseRepository, ExpiresAtMixin, UUIDRepositoryMixin


class AuthorizationCodeRepository(
    BaseRepository[AuthorizationCode],
    UUIDRepositoryMixin[AuthorizationCode],
    ExpiresAtMixin[AuthorizationCode],
):
    model = AuthorizationCode

    async def get_valid_by_code(self, code: str) -> AuthorizationCode | None:
        statement = select(AuthorizationCode).where(
            AuthorizationCode.code == code,
            AuthorizationCode.expires_at > datetime.now(timezone.utc) + timedelta(seconds=-1),
        )
        return await self.get_one_or_none(statement)

    async def get_by_code(self, code: str) -> AuthorizationCode | None:
        statement = select(AuthorizationCode).where(AuthorizationCode.code == code)
        return await self.get_one_or_none(statement)
