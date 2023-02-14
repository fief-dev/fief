from pydantic import UUID4
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from fief.models.base import WorkspaceBase
from fief.models.generics import GUID, CreatedUpdatedAt, ExpiresAt, UUIDModel
from fief.models.user import User
from fief.settings import settings


class SessionToken(UUIDModel, CreatedUpdatedAt, ExpiresAt, WorkspaceBase):
    __tablename__ = "session_tokens"
    __lifetime_seconds__ = settings.session_lifetime_seconds

    token: Mapped[str] = mapped_column(
        String(length=255),
        nullable=False,
        index=True,
        unique=True,
    )

    user_id: Mapped[UUID4] = mapped_column(
        GUID, ForeignKey(User.id, ondelete="CASCADE"), nullable=False
    )
    user: Mapped[User] = relationship("User", lazy="joined")
