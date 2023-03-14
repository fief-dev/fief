from pydantic import UUID4
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.schema import UniqueConstraint

from fief.models.base import WorkspaceBase
from fief.models.generics import GUID, CreatedUpdatedAt, UUIDModel
from fief.models.permission import Permission
from fief.models.role import Role
from fief.models.user import User


class UserPermission(UUIDModel, CreatedUpdatedAt, WorkspaceBase):
    __tablename__ = "user_permissions"
    __table_args__ = (UniqueConstraint("user_id", "permission_id", "from_role_id"),)

    user_id: Mapped[UUID4] = mapped_column(
        GUID, ForeignKey(User.id, ondelete="CASCADE"), nullable=False
    )
    permission_id: Mapped[UUID4] = mapped_column(
        GUID, ForeignKey(Permission.id, ondelete="CASCADE"), nullable=False
    )
    from_role_id: Mapped[UUID4 | None] = mapped_column(
        GUID, ForeignKey(Role.id, ondelete="CASCADE"), nullable=True
    )

    user: Mapped[User] = relationship("User")
    permission: Mapped[Permission] = relationship("Permission")
    from_role: Mapped[Role] = relationship("Role", back_populates="user_permissions")

    def __repr__(self) -> str:
        return f"UserPermission(id={self.id}, user_id={self.user_id}, permission_id={self.permission_id}), from_role_id={self.from_role_id}"
