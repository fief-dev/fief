from typing import Optional

from sqlalchemy import select

from fief.managers.base import BaseManager, UUIDManagerMixin
from fief.models import Tenant


class TenantManager(BaseManager[Tenant], UUIDManagerMixin[Tenant]):
    model = Tenant

    async def get_by_client_id(self, client_id: str) -> Optional[Tenant]:
        statement = select(Tenant).where(Tenant.client_id == client_id)
        return await self.get_one_or_none(statement)
