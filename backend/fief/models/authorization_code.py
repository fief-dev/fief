import secrets
from typing import List, Optional

from sqlalchemy import Column, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql.sqltypes import JSON, String

from fief.models.base import AccountBase
from fief.models.generics import GUID, UUIDModel
from fief.models.user import User


class AuthorizationCode(UUIDModel, AccountBase):
    __tablename__ = "authorization_codes"

    code: str = Column(
        String(length=255),
        default=secrets.token_urlsafe,
        nullable=False,
        index=True,
        unique=True,
    )
    redirect_uri: str = Column(String(length=2048), nullable=False)
    scope: Optional[List[str]] = Column(JSON, nullable=True)

    user_id = Column(GUID, ForeignKey(User.id, ondelete="CASCADE"), nullable=False)
    user: User = relationship("User", cascade="all, delete")
