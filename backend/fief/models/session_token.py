import secrets
from datetime import datetime

from sqlalchemy import TIMESTAMP, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from fief.models.base import AccountBase
from fief.models.generics import GUID, CreatedUpdatedAt, UUIDModel
from fief.models.user import User


class SessionToken(UUIDModel, CreatedUpdatedAt, AccountBase):
    __tablename__ = "session_tokens"

    token: str = Column(
        String(length=255),
        default=secrets.token_urlsafe,
        nullable=False,
        index=True,
        unique=True,
    )
    expires_at: datetime = Column(TIMESTAMP(timezone=True), nullable=False, index=True)

    user_id = Column(GUID, ForeignKey(User.id, ondelete="CASCADE"), nullable=False)
    user: User = relationship("User")
