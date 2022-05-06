from typing import TYPE_CHECKING, Any, Dict, List

from pydantic import UUID4
from sqlalchemy import Boolean, Column, ForeignKey, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import UniqueConstraint

from fief.locale import Translations, get_preferred_translations
from fief.models.base import WorkspaceBase
from fief.models.generics import GUID, CreatedUpdatedAt, UUIDModel
from fief.models.tenant import Tenant

if TYPE_CHECKING:
    from fief.models.user_field_value import UserFieldValue


class User(UUIDModel, CreatedUpdatedAt, WorkspaceBase):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("email", "tenant_id"),)

    if TYPE_CHECKING:
        email: str
        hashed_password: str
        is_active: bool
        is_superuser: bool
        is_verified: bool
    else:
        email: str = Column(String(length=320), index=True, nullable=False)
        hashed_password: str = Column(String(length=255), nullable=False)
        is_active: bool = Column(Boolean, default=True, nullable=False)
        is_superuser: bool = Column(Boolean, default=False, nullable=False)
        is_verified: bool = Column(Boolean, default=False, nullable=False)

    tenant_id: UUID4 = Column(GUID, ForeignKey(Tenant.id, ondelete="CASCADE"), nullable=False)  # type: ignore
    tenant: Tenant = relationship("Tenant")

    user_field_values: List["UserFieldValue"] = relationship(
        "UserFieldValue", back_populates="user", cascade="all, delete", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"User(id={self.id}, email={self.email})"

    def get_fields(self) -> Dict[str, Any]:
        return dict(
            user_field_value.get_slug_and_value()
            for user_field_value in self.user_field_values
        )

    def get_preferred_translations(self) -> Translations:
        return get_preferred_translations([])
