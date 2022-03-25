import secrets
from re import L
from typing import List, Optional

from pydantic import UUID4
from sqlalchemy import Column, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql.sqltypes import JSON, String

from fief.models.base import WorkspaceBase
from fief.models.client import Client
from fief.models.generics import GUID, CreatedUpdatedAt, UUIDModel


class LoginSession(UUIDModel, CreatedUpdatedAt, WorkspaceBase):
    __tablename__ = "login_sessions"

    token: str = Column(
        String(length=255),
        default=secrets.token_urlsafe,
        nullable=False,
        index=True,
        unique=True,
    )
    response_type: str = Column(String(length=255), nullable=False)
    redirect_uri: str = Column(String(length=2048), nullable=False)
    scope: List[str] = Column(JSON, nullable=False, default=list)
    prompt: Optional[str] = Column(String(length=255), nullable=True)
    state: Optional[str] = Column(String(length=2048), nullable=True)
    nonce: Optional[str] = Column(String(length=255), nullable=True)

    client_id: UUID4 = Column(GUID, ForeignKey(Client.id, ondelete="CASCADE"), nullable=False)  # type: ignore
    client: Client = relationship("Client", lazy="joined")
