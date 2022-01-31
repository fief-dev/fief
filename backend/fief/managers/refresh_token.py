from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select

from fief.managers.base import BaseManager, UUIDManagerMixin
from fief.models import RefreshToken


class RefreshTokenManager(BaseManager[RefreshToken], UUIDManagerMixin[RefreshToken]):
    model = RefreshToken

    async def get_by_token(
        self, token: str, *, fresh: bool = True
    ) -> Optional[RefreshToken]:
        statement = select(RefreshToken).where(RefreshToken.token == token)
        if fresh:
            statement = statement.where(
                RefreshToken.expires_at > datetime.now(timezone.utc)
            )

        return await self.get_one_or_none(statement)
