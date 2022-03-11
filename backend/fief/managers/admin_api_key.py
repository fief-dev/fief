from typing import Optional

from sqlalchemy import select

from fief.managers.base import BaseManager, UUIDManagerMixin
from fief.models import AdminAPIKey


class AdminAPIKeyManager(BaseManager[AdminAPIKey], UUIDManagerMixin[AdminAPIKey]):
    model = AdminAPIKey

    async def get_by_token(self, token: str) -> Optional[AdminAPIKey]:
        statement = select(AdminAPIKey).where(AdminAPIKey.token == token)
        return await self.get_one_or_none(statement)
