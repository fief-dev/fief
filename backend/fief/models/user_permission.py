from typing import Optional

from pydantic import UUID4
from sqlalchemy import Column, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import UniqueConstraint

from fief.models.base import WorkspaceBase
from fief.models.generics import GUID, CreatedUpdatedAt, UUIDModel
from fief.models.permission import Permission
from fief.models.role import Role
from fief.models.user import User


class UserPermission(UUIDModel, CreatedUpdatedAt, WorkspaceBase):
    __tablename__ = "user_permissions"
    __table_args__ = (UniqueConstraint("user_id", "permission_id", "from_role_id"),)

    user_id: UUID4 = Column(GUID, ForeignKey(User.id, ondelete="CASCADE"), nullable=False)  # type: ignore
    permission_id: UUID4 = Column(GUID, ForeignKey(Permission.id, ondelete="CASCADE"), nullable=False)  # type: ignore
    from_role_id: Optional[UUID4] = Column(
        GUID, ForeignKey(Role.id, ondelete="CASCADE"), nullable=True  # type: ignore
    )

    user: User = relationship("User")
    permission: Permission = relationship("Permission")
    from_role: Role = relationship("Role", back_populates="user_permissions")

    def __repr__(self) -> str:
        return f"UserPermission(id={self.id}, user_id={self.user_id}, permission_id={self.permission_id}), from_role_id={self.from_role_id}"
