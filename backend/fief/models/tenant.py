from sqlalchemy import Column, String

from fief.models.base import AccountBase
from fief.models.generics import UUIDModel


class Tenant(UUIDModel, AccountBase):
    __tablename__ = "tenants"

    name: str = Column(String(length=255), nullable=False)

    def __repr__(self) -> str:
        return f"Tenant(id={self.id}, name={self.name})"
