import secrets

from pydantic import UUID4
from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.orm import relationship

from fief.models.base import AccountBase
from fief.models.generics import GUID, CreatedUpdatedAt, UUIDModel
from fief.models.tenant import Tenant


class Client(UUIDModel, CreatedUpdatedAt, AccountBase):
    __tablename__ = "clients"

    name: str = Column(String(length=255), nullable=False)

    client_id: str = Column(
        String(length=255), default=secrets.token_urlsafe, nullable=False, index=True
    )
    client_secret: str = Column(
        String(length=255), default=secrets.token_urlsafe, nullable=False, index=True
    )

    tenant_id: UUID4 = Column(GUID, ForeignKey(Tenant.id, ondelete="CASCADE"), nullable=False)  # type: ignore
    tenant: Tenant = relationship("Tenant", lazy="joined")

    def __repr__(self) -> str:
        return f"Client(id={self.id}, name={self.name}, client_id={self.client_id})"
