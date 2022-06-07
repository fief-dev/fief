from pydantic import UUID4
from sqlalchemy import Column, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import UniqueConstraint

from fief.models.base import WorkspaceBase
from fief.models.generics import GUID, CreatedUpdatedAt, UUIDModel
from fief.models.role import Role
from fief.models.user import User


class UserRole(UUIDModel, CreatedUpdatedAt, WorkspaceBase):
    __tablename__ = "user_roles"
    __table_args__ = (UniqueConstraint("user_id", "role_id"),)

    user_id: UUID4 = Column(GUID, ForeignKey(User.id, ondelete="CASCADE"), nullable=False)  # type: ignore
    role_id: UUID4 = Column(GUID, ForeignKey(Role.id, ondelete="CASCADE"), nullable=False)  # type: ignore

    user: User = relationship("User")
    role: Role = relationship("Role")

    def __repr__(self) -> str:
        return f"UserRole(id={self.id}, user_id={self.user_id}, role_id={self.role_id})"
