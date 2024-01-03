from pydantic import UUID4
from sqlalchemy import JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.schema import UniqueConstraint

from fief.models.base import Base
from fief.models.client import Client
from fief.models.generics import GUID, CreatedUpdatedAt, UUIDModel
from fief.models.user import User


class Grant(UUIDModel, CreatedUpdatedAt, Base):
    __tablename__ = "grants"
    __table_args__ = (UniqueConstraint("user_id", "client_id"),)

    scope: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)

    user_id: Mapped[UUID4] = mapped_column(
        GUID, ForeignKey(User.id, ondelete="CASCADE"), nullable=False
    )
    user: Mapped[User] = relationship("User")

    client_id: Mapped[UUID4] = mapped_column(
        GUID, ForeignKey(Client.id, ondelete="CASCADE"), nullable=False
    )
    client: Mapped[Client] = relationship("Client", lazy="joined")
