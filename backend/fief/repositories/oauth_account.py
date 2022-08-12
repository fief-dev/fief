from typing import Optional

from pydantic import UUID4
from sqlalchemy import select

from fief.models import OAuthAccount
from fief.repositories.base import BaseRepository, UUIDRepositoryMixin


class OAuthAccountRepository(
    BaseRepository[OAuthAccount], UUIDRepositoryMixin[OAuthAccount]
):
    model = OAuthAccount

    async def get_by_provider_and_account_id(
        self, provider_id: UUID4, account_id: str
    ) -> Optional[OAuthAccount]:
        statement = select(OAuthAccount).where(
            OAuthAccount.oauth_provider_id == provider_id,
            OAuthAccount.account_id == account_id,
        )
        return await self.get_one_or_none(statement)
