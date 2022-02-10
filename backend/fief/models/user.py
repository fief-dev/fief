from pydantic import UUID4
from sqlalchemy import Boolean, Column, ForeignKey, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import UniqueConstraint

from fief.locale import Translations, get_preferred_translations
from fief.models.base import AccountBase
from fief.models.generics import GUID, CreatedUpdatedAt, UUIDModel
from fief.models.tenant import Tenant


class User(UUIDModel, CreatedUpdatedAt, AccountBase):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("email", "tenant_id"),)

    email: str = Column(String(length=320), index=True, nullable=False)
    hashed_password = Column(String(length=72), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)

    tenant_id: UUID4 = Column(GUID, ForeignKey(Tenant.id, ondelete="CASCADE"), nullable=False)  # type: ignore
    tenant: Tenant = relationship("Tenant")

    def __repr__(self) -> str:
        return f"User(id={self.id}, email={self.email})"

    def get_preferred_translations(self) -> Translations:
        return get_preferred_translations([])
