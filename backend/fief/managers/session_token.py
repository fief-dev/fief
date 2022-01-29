from typing import Optional

from sqlalchemy import select

from fief.managers.base import BaseManager, UUIDManagerMixin
from fief.models import SessionToken


class SessionTokenManager(BaseManager[SessionToken], UUIDManagerMixin[SessionToken]):
    model = SessionToken

    async def get_by_token(self, token: str) -> Optional[SessionToken]:
        statement = select(SessionToken).where(SessionToken.token == token)
        return await self.get_one_or_none(statement)
