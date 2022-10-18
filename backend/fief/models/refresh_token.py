from datetime import datetime
from typing import List

from pydantic import UUID4
from sqlalchemy import JSON, Column, ForeignKey, String
from sqlalchemy.orm import relationship

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
from fief.settings import settings


class RefreshToken(UUIDModel, CreatedUpdatedAt, ExpiresAt, WorkspaceBase):
    __tablename__ = "refresh_tokens"
    __lifetime_seconds__ = settings.refresh_token_lifetime_seconds

    token: str = Column(
        String(length=255),
        nullable=False,
        index=True,
        unique=True,
    )
    scope: List[str] = Column(JSON, nullable=False, default=list)
    authenticated_at: datetime = Column(TIMESTAMPAware(timezone=True), nullable=False)

    user_id: UUID4 = Column(
        GUID, ForeignKey(User.id, ondelete="CASCADE"), nullable=False
    )
    user: User = relationship("User")

    client_id: UUID4 = Column(
        GUID, ForeignKey(Client.id, ondelete="CASCADE"), nullable=False
    )
    client: Client = relationship("Client", lazy="joined")
