from pydantic import UUID4
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from fief.models.base import MainBase
from fief.models.generics import GUID, CreatedUpdatedAt, UUIDModel
from fief.models.workspace import Workspace


class WorkspaceUser(UUIDModel, CreatedUpdatedAt, MainBase):
    __tablename__ = "workspace_users"

    workspace_id: Mapped[UUID4] = mapped_column(
        GUID, ForeignKey(Workspace.id, ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[UUID4] = mapped_column(GUID, nullable=False)

    workspace: Mapped[Workspace] = relationship(
        "Workspace", back_populates="workspace_users", lazy="joined"
    )

    def __repr__(self) -> str:
        return f"WorkspaceUser(id={self.id}, workspace_id={self.workspace_id}, user_id={self.user_id})"
