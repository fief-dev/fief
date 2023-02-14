from pydantic import UUID4
from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from fief.models.base import MainBase
from fief.models.generics import GUID, CreatedUpdatedAt, UUIDModel
from fief.models.workspace import Workspace


class AdminAPIKey(UUIDModel, CreatedUpdatedAt, MainBase):
    __tablename__ = "admin_api_key"

    name: Mapped[str] = mapped_column(String(length=255), nullable=False)
    token: Mapped[str] = mapped_column(String(length=255), unique=True, nullable=False)
    workspace_id: Mapped[UUID4] = mapped_column(
        GUID, ForeignKey(Workspace.id, ondelete="CASCADE"), nullable=False
    )

    def __repr__(self) -> str:
        return f"AdminAPIKey(id={self.id})"
