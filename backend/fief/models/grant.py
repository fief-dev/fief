from typing import List

from pydantic import UUID4
from sqlalchemy import JSON, Column, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import UniqueConstraint

from fief.models.base import WorkspaceBase
from fief.models.client import Client
from fief.models.generics import GUID, CreatedUpdatedAt, UUIDModel
from fief.models.user import User


class Grant(UUIDModel, CreatedUpdatedAt, WorkspaceBase):
    __tablename__ = "grants"
    __table_args__ = (UniqueConstraint("user_id", "client_id"),)

    scope: List[str] = Column(JSON, nullable=False, default=list)

    user_id: UUID4 = Column(GUID, ForeignKey(User.id, ondelete="CASCADE"), nullable=False)  # type: ignore
    user: User = relationship("User")

    client_id: UUID4 = Column(GUID, ForeignKey(Client.id, ondelete="CASCADE"), nullable=False)  # type: ignore
    client: Client = relationship("Client", lazy="joined")
