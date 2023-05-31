from sqlalchemy import select

from fief.models import EmailDomain
from fief.repositories.base import BaseRepository, UUIDRepositoryMixin


class EmailDomainRepository(
    BaseRepository[EmailDomain], UUIDRepositoryMixin[EmailDomain]
):
    model = EmailDomain

    async def get_by_domain(self, domain: str) -> EmailDomain | None:
        statement = select(EmailDomain).where(EmailDomain.domain == domain)
        return await self.get_one_or_none(statement)
