from typing import Optional

from sqlalchemy import select

from fief.managers.base import BaseManager, UUIDManagerMixin
from fief.models import AuthorizationCode


class AuthorizationCodeManager(
    BaseManager[AuthorizationCode], UUIDManagerMixin[AuthorizationCode]
):
    model = AuthorizationCode

    async def get_by_code(self, code: str) -> Optional[AuthorizationCode]:
        statement = select(AuthorizationCode).where(AuthorizationCode.code == code)
        return await self.get_one_or_none(statement)
