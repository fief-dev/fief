from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select

from fief.models import AuthorizationCode
from fief.repositories.base import BaseRepository, UUIDRepositoryMixin
from fief.settings import settings


class AuthorizationCodeRepository(
    BaseRepository[AuthorizationCode], UUIDRepositoryMixin[AuthorizationCode]
):
    model = AuthorizationCode

    async def get_valid_by_code(self, code: str) -> Optional[AuthorizationCode]:
        max_created_at = datetime.now(timezone.utc) - timedelta(
            seconds=settings.authorization_code_lifetime_seconds
        )
        statement = select(AuthorizationCode).where(
            AuthorizationCode.code == code,
            AuthorizationCode.created_at > max_created_at,
        )
        return await self.get_one_or_none(statement)

    async def get_by_code(self, code: str) -> Optional[AuthorizationCode]:
        statement = select(AuthorizationCode).where(AuthorizationCode.code == code)
        return await self.get_one_or_none(statement)
