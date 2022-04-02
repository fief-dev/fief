from datetime import datetime
from typing import List

from pydantic import UUID4
from sqlalchemy import JSON, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from fief.models.base import WorkspaceBase
from fief.models.client import Client
from fief.models.generics import GUID, CreatedUpdatedAt, TIMESTAMPAware, UUIDModel
from fief.models.user import User


class RefreshToken(UUIDModel, CreatedUpdatedAt, WorkspaceBase):
    __tablename__ = "refresh_tokens"

    token: str = Column(
        String(length=255),
        nullable=False,
        index=True,
        unique=True,
    )
    expires_at: datetime = Column(
        TIMESTAMPAware(timezone=True), nullable=False, index=True
    )
    scope: List[str] = Column(JSON, nullable=False, default=list)
    authenticated_at: datetime = Column(TIMESTAMPAware(timezone=True), nullable=False)

    user_id: UUID4 = Column(GUID, ForeignKey(User.id, ondelete="CASCADE"), nullable=False)  # type: ignore
    user: User = relationship("User")

    client_id: UUID4 = Column(GUID, ForeignKey(Client.id, ondelete="CASCADE"), nullable=False)  # type: ignore
    client: Client = relationship("Client", lazy="joined")
