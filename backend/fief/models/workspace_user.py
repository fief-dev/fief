from pydantic import UUID4
from sqlalchemy import Column, ForeignKey
from sqlalchemy.orm import relationship

from fief.models.base import MainBase
from fief.models.generics import GUID, CreatedUpdatedAt, UUIDModel
from fief.models.workspace import Workspace


class WorkspaceUser(UUIDModel, CreatedUpdatedAt, MainBase):
    __tablename__ = "workspace_users"

    workspace_id: UUID4 = Column(GUID, ForeignKey(Workspace.id, ondelete="CASCADE"), nullable=False)  # type: ignore
    user_id: UUID4 = Column(GUID, nullable=False)

    workspace: Workspace = relationship(
        "Workspace", back_populates="workspace_users", lazy="joined"
    )

    def __repr__(self) -> str:
        return f"WorkspaceUser(id={self.id}, workspace_id={self.workspace_id}, user_id={self.user_id})"
