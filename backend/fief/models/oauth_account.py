from datetime import datetime, timezone
from typing import Optional

from pydantic import UUID4
from sqlalchemy import Column, ForeignKey, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import UniqueConstraint

from fief.crypto.encryption import FernetEngine, StringEncryptedType
from fief.models.base import WorkspaceBase
from fief.models.generics import GUID, CreatedUpdatedAt, TIMESTAMPAware, UUIDModel
from fief.models.oauth_provider import OAuthProvider
from fief.models.tenant import Tenant
from fief.models.user import User
from fief.settings import settings


class OAuthAccount(UUIDModel, CreatedUpdatedAt, WorkspaceBase):
    __tablename__ = "oauth_accounts"
    __table_args__ = (UniqueConstraint("oauth_provider_id", "user_id"),)

    access_token: str = Column(
        StringEncryptedType(Text, settings.encryption_key, FernetEngine), nullable=False
    )
    expires_at: Optional[datetime] = Column(
        TIMESTAMPAware(timezone=True), nullable=True
    )
    refresh_token: Optional[str] = Column(
        StringEncryptedType(Text, settings.encryption_key, FernetEngine), nullable=True
    )
    account_id: str = Column(String(length=1024), index=True, nullable=False)
    account_email: Optional[str] = Column(String(length=1024), nullable=True)

    oauth_provider_id: UUID4 = Column(
        GUID, ForeignKey(OAuthProvider.id, ondelete="CASCADE"), nullable=False
    )
    oauth_provider: OAuthProvider = relationship("OAuthProvider", lazy="joined")

    user_id: Optional[UUID4] = Column(
        GUID, ForeignKey(User.id, ondelete="CASCADE"), nullable=True
    )
    user: Optional[User] = relationship("User", lazy="joined")

    tenant_id: UUID4 = Column(
        GUID, ForeignKey(Tenant.id, ondelete="CASCADE"), nullable=False
    )
    tenant: Tenant = relationship("Tenant")

    def is_expired(self) -> bool:
        return self.expires_at is not None and self.expires_at < datetime.now(
            timezone.utc
        )
