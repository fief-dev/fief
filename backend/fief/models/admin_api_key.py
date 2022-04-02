from pydantic import UUID4
from sqlalchemy import Column, ForeignKey, String

from fief.models.base import MainBase
from fief.models.generics import GUID, CreatedUpdatedAt, UUIDModel
from fief.models.workspace import Workspace


class AdminAPIKey(UUIDModel, CreatedUpdatedAt, MainBase):
    __tablename__ = "admin_api_key"

    name: str = Column(String(length=255), nullable=False)
    token: str = Column(String(length=255), unique=True, nullable=False)
    workspace_id: UUID4 = Column(GUID, ForeignKey(Workspace.id, ondelete="CASCADE"), nullable=False)  # type: ignore

    def __repr__(self) -> str:
        return f"AdminAPIKey(id={self.id})"
