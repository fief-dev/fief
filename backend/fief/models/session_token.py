import secrets
from datetime import datetime

from pydantic import UUID4
from sqlalchemy import TIMESTAMP, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from fief.models.base import WorkspaceBase
from fief.models.generics import GUID, CreatedUpdatedAt, UUIDModel
from fief.models.user import User


class SessionToken(UUIDModel, CreatedUpdatedAt, WorkspaceBase):
    __tablename__ = "session_tokens"

    token: str = Column(
        String(length=255),
        default=secrets.token_urlsafe,
        nullable=False,
        index=True,
        unique=True,
    )
    expires_at: datetime = Column(TIMESTAMP(timezone=True), nullable=False, index=True)

    user_id: UUID4 = Column(GUID, ForeignKey(User.id, ondelete="CASCADE"), nullable=False)  # type: ignore
    user: User = relationship("User")
