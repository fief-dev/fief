from typing import Optional

from sqlalchemy import select

from fief.managers.base import BaseManager, UUIDManagerMixin
from fief.models import Account


class AccountManager(BaseManager[Account], UUIDManagerMixin[Account]):
    model = Account

    async def get_by_domain(self, domain: str) -> Optional[Account]:
        statement = select(Account).where(Account.domain == domain)
        return await self.get_one_or_none(statement)
