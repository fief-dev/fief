import random
import string
from typing import Optional

from slugify import slugify
from sqlalchemy import select

from fief.managers.base import BaseManager, UUIDManagerMixin
from fief.models import Account
from fief.settings import settings


class AccountManager(BaseManager[Account], UUIDManagerMixin[Account]):
    model = Account

    async def get_by_domain(self, domain: str) -> Optional[Account]:
        statement = select(Account).where(Account.domain == domain)
        return await self.get_one_or_none(statement)

    async def get_available_subdomain(self, name: str) -> str:
        slug = slugify(name)
        domain = f"{slug}.{settings.root_domain}"
        account = await self.get_by_domain(domain)

        if account is None:
            return domain

        random_string = "".join(
            random.choices(string.ascii_lowercase + string.digits, k=6)
        )
        return f"{slug}-{random_string}.{settings.root_domain}"
