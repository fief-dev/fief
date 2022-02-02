from typing import Optional

from sqlalchemy import select

from fief.managers.base import BaseManager, UUIDManagerMixin
from fief.models import AdminSessionToken


class AdminSessionTokenManager(
    BaseManager[AdminSessionToken], UUIDManagerMixin[AdminSessionToken]
):
    model = AdminSessionToken

    async def get_by_token(self, token: str) -> Optional[AdminSessionToken]:
        statement = select(AdminSessionToken).where(AdminSessionToken.token == token)
        return await self.get_one_or_none(statement)
