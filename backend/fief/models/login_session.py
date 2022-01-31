import secrets
from typing import List, Optional

from sqlalchemy import Column, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql.sqltypes import JSON, String

from fief.models.base import AccountBase
from fief.models.client import Client
from fief.models.generics import GUID, CreatedUpdatedAt, UUIDModel


class LoginSession(UUIDModel, CreatedUpdatedAt, AccountBase):
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
    state: Optional[str] = Column(String(length=2048), nullable=True)

    client_id = Column(GUID, ForeignKey(Client.id, ondelete="CASCADE"), nullable=False)
    client: Client = relationship("Client", lazy="joined")
