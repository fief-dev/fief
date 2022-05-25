from sqlalchemy import Column, String

from fief.models.base import WorkspaceBase
from fief.models.generics import CreatedUpdatedAt, UUIDModel


class Permission(UUIDModel, CreatedUpdatedAt, WorkspaceBase):
    __tablename__ = "permissions"

    name: str = Column(String(length=255), nullable=False)
    codename: str = Column(String(length=255), nullable=False, unique=True)

    def __repr__(self) -> str:
        return f"Permission(id={self.id}, name={self.name}, codename={self.codename}"
