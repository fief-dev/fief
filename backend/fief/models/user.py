from sqlalchemy import Boolean, Column, ForeignKey, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import UniqueConstraint

from fief.models.base import AccountBase
from fief.models.generics import GUID, UUIDModel
from fief.models.tenant import Tenant


class User(UUIDModel, AccountBase):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("email", "tenant_id"),)

    email = Column(String(length=320), index=True, nullable=False)
    hashed_password = Column(String(length=72), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)

    tenant_id = Column(GUID, ForeignKey(Tenant.id, ondelete="CASCADE"), nullable=False)
    tenant: Tenant = relationship("Tenant", cascade="all, delete")

    def __repr__(self) -> str:
        return f"User(id={self.id}, email={self.email})"
