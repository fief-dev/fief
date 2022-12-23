import secrets

from pydantic import UUID4
from sqlalchemy import Column, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql.sqltypes import String

from fief.models.base import WorkspaceBase
from fief.models.generics import GUID, CreatedUpdatedAt, ExpiresAt, UUIDModel
from fief.models.login_session import LoginSession
from fief.models.oauth_account import OAuthAccount
from fief.models.oauth_provider import OAuthProvider
from fief.models.tenant import Tenant
from fief.settings import settings


class OAuthSession(UUIDModel, CreatedUpdatedAt, ExpiresAt, WorkspaceBase):
    __tablename__ = "oauth_sessions"
    __lifetime_seconds__ = settings.login_session_lifetime_seconds

    token: str = Column(
        String(length=255),
        default=secrets.token_urlsafe,
        nullable=False,
        index=True,
        unique=True,
    )
    redirect_uri: str = Column(Text, nullable=False)

    oauth_provider_id: UUID4 = Column(
        GUID, ForeignKey(OAuthProvider.id, ondelete="CASCADE"), nullable=False
    )
    oauth_provider: OAuthProvider = relationship("OAuthProvider", lazy="joined")

    login_session_id: UUID4 = Column(
        GUID, ForeignKey(LoginSession.id, ondelete="CASCADE"), nullable=False
    )
    login_session: LoginSession = relationship("LoginSession")

    oauth_account_id: UUID4 | None = Column(
        GUID, ForeignKey(OAuthAccount.id, ondelete="CASCADE"), nullable=True
    )
    oauth_account: OAuthAccount | None = relationship("OAuthAccount", lazy="joined")

    tenant_id: UUID4 = Column(
        GUID, ForeignKey(Tenant.id, ondelete="CASCADE"), nullable=False
    )
    tenant: Tenant = relationship("Tenant", lazy="joined")
