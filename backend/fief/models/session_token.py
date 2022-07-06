from pydantic import UUID4
from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.orm import relationship

from fief.models.base import WorkspaceBase
from fief.models.generics import GUID, CreatedUpdatedAt, ExpiresAt, UUIDModel
from fief.models.user import User
from fief.settings import settings


class SessionToken(UUIDModel, CreatedUpdatedAt, ExpiresAt, WorkspaceBase):
    __tablename__ = "session_tokens"
    __lifetime_seconds__ = settings.session_lifetime_seconds

    token: str = Column(
        String(length=255),
        nullable=False,
        index=True,
        unique=True,
    )

    user_id: UUID4 = Column(GUID, ForeignKey(User.id, ondelete="CASCADE"), nullable=False)  # type: ignore
    user: User = relationship("User", lazy="joined")
