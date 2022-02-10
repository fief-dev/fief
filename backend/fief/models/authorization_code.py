import secrets
from typing import List

from pydantic import UUID4
from sqlalchemy import Column, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql.sqltypes import JSON, String

from fief.models.base import AccountBase
from fief.models.client import Client
from fief.models.generics import GUID, CreatedUpdatedAt, UUIDModel
from fief.models.user import User


class AuthorizationCode(UUIDModel, CreatedUpdatedAt, AccountBase):
    __tablename__ = "authorization_codes"

    code: str = Column(
        String(length=255),
        default=secrets.token_urlsafe,
        nullable=False,
        index=True,
        unique=True,
    )
    redirect_uri: str = Column(String(length=2048), nullable=False)
    scope: List[str] = Column(JSON, nullable=False, default=list)

    user_id: UUID4 = Column(GUID, ForeignKey(User.id, ondelete="CASCADE"), nullable=False)  # type: ignore
    user: User = relationship("User")

    client_id: UUID4 = Column(GUID, ForeignKey(Client.id, ondelete="CASCADE"), nullable=False)  # type: ignore
    client: Client = relationship("Client", lazy="joined")
