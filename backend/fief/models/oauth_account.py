from datetime import datetime, timezone
from typing import Optional

from pydantic import UUID4
from sqlalchemy import Column, ForeignKey, String, Text
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import UniqueConstraint

from fief.crypto.encryption import decrypt, encrypt
from fief.models.base import WorkspaceBase
from fief.models.generics import GUID, CreatedUpdatedAt, TIMESTAMPAware, UUIDModel
from fief.models.oauth_provider import OAuthProvider
from fief.models.tenant import Tenant
from fief.models.user import User
from fief.settings import settings


class OAuthAccount(UUIDModel, CreatedUpdatedAt, WorkspaceBase):
    __tablename__ = "oauth_accounts"
    __table_args__ = (UniqueConstraint("oauth_provider_id", "user_id"),)

    _access_token: str = Column("access_token", Text, nullable=False)
    expires_at: Optional[datetime] = Column(
        TIMESTAMPAware(timezone=True), nullable=True
    )
    _refresh_token: Optional[str] = Column("refresh_token", Text, nullable=True)
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

    def __init__(self, *args, **kwargs) -> None:
        access_token = kwargs.pop("access_token", None)
        self.access_token = access_token  # type: ignore
        refresh_token = kwargs.pop("refresh_token", None)
        self.refresh_token = refresh_token  # type: ignore
        super().__init__(*args, **kwargs)

    @hybrid_property
    def access_token(self):
        return decrypt(self._access_token, settings.encryption_key)

    @access_token.setter  # type: ignore
    def access_token(self, value: str):
        self._access_token = encrypt(value, settings.encryption_key)

    @hybrid_property
    def refresh_token(self) -> Optional[str]:
        if self._refresh_token is not None:
            return decrypt(self._refresh_token, settings.encryption_key)
        return None

    @refresh_token.setter  # type: ignore
    def refresh_token(self, value: Optional[str]):
        if value is not None:
            self._refresh_token = encrypt(value, settings.encryption_key)
        else:
            self._refresh_token = None

    def is_expired(self) -> bool:
        return self.expires_at is not None and self.expires_at < datetime.now(
            timezone.utc
        )
