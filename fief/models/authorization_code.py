from datetime import datetime
from typing import cast

from pydantic import UUID4
from sqlalchemy import Column, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql.sqltypes import JSON, String

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


class AuthorizationCode(UUIDModel, CreatedUpdatedAt, ExpiresAt, WorkspaceBase):
    __tablename__ = "authorization_codes"

    code: str = Column(
        String(length=255),
        nullable=False,
        index=True,
        unique=True,
    )
    c_hash: str = Column(String(length=255), nullable=False)
    redirect_uri: str = Column(String(length=2048), nullable=False)
    scope: list[str] = Column(JSON, nullable=False, default=list)
    authenticated_at: datetime = Column(TIMESTAMPAware(timezone=True), nullable=False)
    nonce: str | None = Column(String(length=255), nullable=True)
    code_challenge: str | None = Column(String(length=255), nullable=True)
    code_challenge_method: str | None = Column(String(length=255), nullable=True)

    user_id: UUID4 = Column(
        GUID, ForeignKey(User.id, ondelete="CASCADE"), nullable=False
    )
    user: User = relationship("User")

    client_id: UUID4 = Column(
        GUID, ForeignKey(Client.id, ondelete="CASCADE"), nullable=False
    )
    client: Client = relationship("Client", lazy="joined")

    def get_code_challenge_tuple(self) -> tuple[str, str] | None:
        if self.code_challenge is not None:
            return (self.code_challenge, cast(str, self.code_challenge_method))
        return None
