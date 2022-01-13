from typing import Optional

from sqlalchemy import select

from fief.managers.base import BaseManager, UUIDManagerMixin
from fief.models import Client


class ClientManager(BaseManager[Client], UUIDManagerMixin[Client]):
    model = Client

    async def get_by_client_id(self, client_id: str) -> Optional[Client]:
        statement = select(Client).where(Client.client_id == client_id)
        return await self.get_one_or_none(statement)

    async def get_by_client_id_and_secret(
        self, client_id: str, client_secret: str
    ) -> Optional[Client]:
        statement = select(Client).where(
            Client.client_id == client_id, Client.client_secret == client_secret
        )
        return await self.get_one_or_none(statement)
