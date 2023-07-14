from pydantic import UUID4
from sqlalchemy import select

from fief.models import EmailVerification
from fief.repositories.base import BaseRepository, ExpiresAtMixin, UUIDRepositoryMixin


class EmailVerificationRepository(
    BaseRepository[EmailVerification],
    UUIDRepositoryMixin[EmailVerification],
    ExpiresAtMixin[EmailVerification],
):
    model = EmailVerification

    async def get_by_code_and_user(
        self, code: str, user: UUID4
    ) -> EmailVerification | None:
        statement = select(EmailVerification).where(
            EmailVerification.code == code, EmailVerification.user_id == user
        )
        return await self.get_one_or_none(statement)

    async def get_last(self) -> EmailVerification | None:
        statement = (
            select(EmailVerification)
            .order_by(EmailVerification.created_at.desc())
            .limit(1)
        )
        return await self.get_one_or_none(statement)
