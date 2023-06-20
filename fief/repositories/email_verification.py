from sqlalchemy import select

from fief.models import EmailVerification
from fief.repositories.base import BaseRepository, ExpiresAtMixin, UUIDRepositoryMixin


class EmailVerificationRepository(
    BaseRepository[EmailVerification],
    UUIDRepositoryMixin[EmailVerification],
    ExpiresAtMixin[EmailVerification],
):
    model = EmailVerification

    async def get_by_code(self, code: str) -> EmailVerification | None:
        statement = select(EmailVerification).where(EmailVerification.code == code)
        return await self.get_one_or_none(statement)
