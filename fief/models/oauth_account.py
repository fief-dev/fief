from datetime import UTC, datetime

from pydantic import UUID4
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.schema import UniqueConstraint

from fief.crypto.encryption import FernetEngine, StringEncryptedType
from fief.models.base import Base
from fief.models.generics import GUID, CreatedUpdatedAt, TIMESTAMPAware, UUIDModel
from fief.models.oauth_provider import OAuthProvider
from fief.models.tenant import Tenant
from fief.models.user import User
from fief.settings import settings


class OAuthAccount(UUIDModel, CreatedUpdatedAt, Base):
    __tablename__ = "oauth_accounts"
    __table_args__ = (
        UniqueConstraint("oauth_provider_id", "user_id"),
        UniqueConstraint("oauth_provider_id", "account_id"),
    )

    access_token: Mapped[str] = mapped_column(
        StringEncryptedType(Text, settings.encryption_key, FernetEngine), nullable=False
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMPAware(timezone=True), nullable=True
    )
    refresh_token: Mapped[str | None] = mapped_column(
        StringEncryptedType(Text, settings.encryption_key, FernetEngine), nullable=True
    )
    account_id: Mapped[str] = mapped_column(
        String(length=512), index=True, nullable=False
    )
    account_email: Mapped[str | None] = mapped_column(String(length=512), nullable=True)

    oauth_provider_id: Mapped[UUID4] = mapped_column(
        GUID, ForeignKey(OAuthProvider.id, ondelete="CASCADE"), nullable=False
    )
    oauth_provider: Mapped[OAuthProvider] = relationship("OAuthProvider", lazy="joined")

    user_id: Mapped[UUID4 | None] = mapped_column(
        GUID, ForeignKey(User.id, ondelete="CASCADE"), nullable=True
    )
    user: Mapped[User | None] = relationship("User", lazy="joined")

    tenant_id: Mapped[UUID4] = mapped_column(
        GUID, ForeignKey(Tenant.id, ondelete="CASCADE"), nullable=False
    )
    tenant: Mapped[Tenant] = relationship("Tenant")

    def is_expired(self) -> bool:
        return self.expires_at is not None and self.expires_at < datetime.now(UTC)
