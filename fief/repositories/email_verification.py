from pydantic import UUID4
from sqlalchemy import delete, select

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

    async def delete_by_user(self, user: UUID4) -> None:
        statement = delete(EmailVerification).where(EmailVerification.user_id == user)
        await self._execute_statement(statement)

    async def get_by_user(self, user: UUID4) -> list[EmailVerification]:
        statement = select(EmailVerification).where(EmailVerification.user_id == user)
        return await self.list(statement)
