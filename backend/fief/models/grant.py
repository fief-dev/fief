from typing import List

from sqlalchemy import JSON, Column, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import UniqueConstraint

from fief.models.base import AccountBase
from fief.models.client import Client
from fief.models.generics import GUID, CreatedUpdatedAt, UUIDModel
from fief.models.user import User


class Grant(UUIDModel, CreatedUpdatedAt, AccountBase):
    __tablename__ = "grants"
    __table_args__ = (UniqueConstraint("user_id", "client_id"),)

    scope: List[str] = Column(JSON, nullable=False, default=list)

    user_id = Column(GUID, ForeignKey(User.id, ondelete="CASCADE"), nullable=False)
    user: User = relationship("User")

    client_id = Column(GUID, ForeignKey(Client.id, ondelete="CASCADE"), nullable=False)
    client: Client = relationship("Client", lazy="joined")
