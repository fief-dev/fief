from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from fief.models.base import WorkspaceBase
from fief.models.generics import CreatedUpdatedAt, UUIDModel


class Permission(UUIDModel, CreatedUpdatedAt, WorkspaceBase):
    __tablename__ = "permissions"

    name: Mapped[str] = mapped_column(String(length=255), nullable=False)
    codename: Mapped[str] = mapped_column(
        String(length=255), nullable=False, unique=True
    )

    def __repr__(self) -> str:
        return f"Permission(id={self.id}, name={self.name}, codename={self.codename})"
