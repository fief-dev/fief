from datetime import datetime
from typing import List, Optional, Tuple, cast

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
from fief.settings import settings


class AuthorizationCode(UUIDModel, CreatedUpdatedAt, ExpiresAt, WorkspaceBase):
    __tablename__ = "authorization_codes"
    __lifetime_seconds__ = settings.authorization_code_lifetime_seconds

    code: str = Column(
        String(length=255),
        nullable=False,
        index=True,
        unique=True,
    )
    c_hash: str = Column(String(length=255), nullable=False)
    redirect_uri: str = Column(String(length=2048), nullable=False)
    scope: List[str] = Column(JSON, nullable=False, default=list)
    authenticated_at: datetime = Column(TIMESTAMPAware(timezone=True), nullable=False)
    nonce: Optional[str] = Column(String(length=255), nullable=True)
    code_challenge: Optional[str] = Column(String(length=255), nullable=True)
    code_challenge_method: Optional[str] = Column(String(length=255), nullable=True)

    user_id: UUID4 = Column(GUID, ForeignKey(User.id, ondelete="CASCADE"), nullable=False)  # type: ignore
    user: User = relationship("User")

    client_id: UUID4 = Column(GUID, ForeignKey(Client.id, ondelete="CASCADE"), nullable=False)  # type: ignore
    client: Client = relationship("Client", lazy="joined")

    def get_code_challenge_tuple(self) -> Optional[Tuple[str, str]]:
        if self.code_challenge is not None:
            return (self.code_challenge, cast(str, self.code_challenge_method))
        return None
