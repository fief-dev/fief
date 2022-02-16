from pydantic import UUID4
from sqlalchemy import Column, ForeignKey
from sqlalchemy.orm import relationship

from fief.models.account import Account
from fief.models.base import GlobalBase
from fief.models.generics import GUID, CreatedUpdatedAt, UUIDModel


class AccountUser(UUIDModel, CreatedUpdatedAt, GlobalBase):
    __tablename__ = "account_users"

    account_id: UUID4 = Column(GUID, ForeignKey(Account.id, ondelete="CASCADE"), nullable=False)  # type: ignore
    user_id: UUID4 = Column(GUID, nullable=False)

    account: Account = relationship(
        "Account", back_populates="account_users", lazy="joined"
    )

    def __repr__(self) -> str:
        return f"AccountUser(id={self.id}, account_id={self.account_id}, user_id={self.user_id})"
