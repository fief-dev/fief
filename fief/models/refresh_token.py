from datetime import datetime

from pydantic import UUID4
from sqlalchemy import JSON, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from fief.models.base import WorkspaceBase
from fief.models.client import Client
from fief.models.generics import (
    GUID,
    CreatedUpdatedAt,
    ExpiresAt,
    TIMESTAMPAware,
    UUIDModel,
)
from fief.models.user import User


class RefreshToken(UUIDModel, CreatedUpdatedAt, ExpiresAt, WorkspaceBase):
    __tablename__ = "refresh_tokens"

    token: Mapped[str] = mapped_column(
        String(length=255),
        nullable=False,
        index=True,
        unique=True,
    )
    scope: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    authenticated_at: Mapped[datetime] = mapped_column(
        TIMESTAMPAware(timezone=True), nullable=False
    )

    user_id: Mapped[UUID4] = mapped_column(
        GUID, ForeignKey(User.id, ondelete="CASCADE"), nullable=False
    )
    user: Mapped[User] = relationship("User")

    client_id: Mapped[UUID4] = mapped_column(
        GUID, ForeignKey(Client.id, ondelete="CASCADE"), nullable=False
    )
    client: Mapped[Client] = relationship("Client", lazy="joined")
