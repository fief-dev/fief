import secrets

from sqlalchemy import Boolean, Column, String

from fief.models.base import AccountBase
from fief.models.generics import UUIDModel


class Tenant(UUIDModel, AccountBase):
    __tablename__ = "tenants"

    name: str = Column(String(length=255), nullable=False)
    default: bool = Column(Boolean, default=False, nullable=False)

    client_id: str = Column(
        String(length=255), default=secrets.token_urlsafe, nullable=False, index=True
    )
    client_secret: str = Column(
        String(length=255), default=secrets.token_urlsafe, nullable=False, index=True
    )

    def __repr__(self) -> str:
        return f"Tenant(id={self.id}, name={self.name}, default={self.default})"
