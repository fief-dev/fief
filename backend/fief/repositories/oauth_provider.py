from typing import List

from sqlalchemy import select

from fief.models import OAuthProvider
from fief.repositories.base import BaseRepository, UUIDRepositoryMixin


class OAuthProviderRepository(
    BaseRepository[OAuthProvider], UUIDRepositoryMixin[OAuthProvider]
):
    model = OAuthProvider

    async def all_by_name_and_provider(self) -> List[OAuthProvider]:
        return await self.list(
            select(OAuthProvider).order_by(OAuthProvider.name, OAuthProvider.provider)
        )
