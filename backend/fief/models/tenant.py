import secrets

from sqlalchemy import Boolean, Column, String

from fief.models.base import AccountBase
from fief.models.generics import UUIDModel


class Tenant(UUIDModel, AccountBase):
    __tablename__ = "tenants"

    name: str = Column(String(length=255), nullable=False)
    slug: str = Column(String(length=255), nullable=False, unique=True)
    default: bool = Column(Boolean, default=False, nullable=False)

    def __repr__(self) -> str:
        return f"Tenant(id={self.id}, name={self.name}, slug={self.slug}, default={self.default})"
