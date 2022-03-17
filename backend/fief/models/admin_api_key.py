import secrets

from pydantic import UUID4
from sqlalchemy import Column, ForeignKey, String

from fief.models.account import Account
from fief.models.base import MainBase
from fief.models.generics import GUID, CreatedUpdatedAt, UUIDModel


class AdminAPIKey(UUIDModel, CreatedUpdatedAt, MainBase):
    __tablename__ = "admin_api_key"

    name: str = Column(String(length=255), nullable=False)
    token: str = Column(
        String(length=255), default=secrets.token_urlsafe, unique=True, nullable=False
    )
    account_id: UUID4 = Column(GUID, ForeignKey(Account.id, ondelete="CASCADE"), nullable=False)  # type: ignore

    def __repr__(self) -> str:
        return f"AdminAPIKey(id={self.id})"
