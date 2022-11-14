from pydantic import UUID4
from sqlalchemy import select
from sqlalchemy.sql import Select

from fief.models import OAuthAccount
from fief.repositories.base import BaseRepository, UUIDRepositoryMixin


class OAuthAccountRepository(
    BaseRepository[OAuthAccount], UUIDRepositoryMixin[OAuthAccount]
):
    model = OAuthAccount

    async def get_by_provider_and_account_id(
        self, provider_id: UUID4, account_id: str
    ) -> OAuthAccount | None:
        statement = select(OAuthAccount).where(
            OAuthAccount.oauth_provider_id == provider_id,
            OAuthAccount.account_id == account_id,
        )
        return await self.get_one_or_none(statement)

    async def get_by_provider_and_user(
        self, provider_id: UUID4, user: UUID4
    ) -> OAuthAccount | None:
        statement = select(OAuthAccount).where(
            OAuthAccount.oauth_provider_id == provider_id,
            OAuthAccount.user_id == user,
        )
        return await self.get_one_or_none(statement)

    def get_by_user_statement(self, user: UUID4) -> Select:
        statement = select(OAuthAccount).where(OAuthAccount.user_id == user)
        return statement
