from typing import Optional

from sqlalchemy import select

from fief.managers.base import BaseManager, UUIDManagerMixin
from fief.models import LoginSession


class LoginSessionManager(BaseManager[LoginSession], UUIDManagerMixin[LoginSession]):
    model = LoginSession

    async def get_by_token(self, token: str) -> Optional[LoginSession]:
        statement = select(LoginSession).where(LoginSession.token == token)
        return await self.get_one_or_none(statement)
