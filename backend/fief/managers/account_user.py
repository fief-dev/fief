from typing import Optional

from pydantic import UUID4
from sqlalchemy import select

from fief.managers.base import BaseManager, UUIDManagerMixin
from fief.models import AccountUser


class AccountUserManager(BaseManager[AccountUser], UUIDManagerMixin[AccountUser]):
    model = AccountUser

    async def get_by_account_and_user(
        self, account_id: UUID4, user_id: UUID4
    ) -> Optional[AccountUser]:
        statement = select(AccountUser).where(
            AccountUser.account_id == account_id, AccountUser.user_id == user_id
        )
        return await self.get_one_or_none(statement)
