import secrets

from pydantic import UUID4
from sqlalchemy import Column, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql.sqltypes import String

from fief.models.base import WorkspaceBase
from fief.models.generics import GUID, CreatedUpdatedAt, ExpiresAt, UUIDModel
from fief.models.login_session import LoginSession
from fief.models.oauth_provider import OAuthProvider
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

    oauth_provider_id: UUID4 = Column(GUID, ForeignKey(OAuthProvider.id, ondelete="CASCADE"), nullable=False)  # type: ignore
    oauth_provider: OAuthProvider = relationship("OAuthProvider", lazy="joined")

    login_session_id: UUID4 = Column(GUID, ForeignKey(LoginSession.id, ondelete="CASCADE"), nullable=False)  # type: ignore
    login_session: LoginSession = relationship("LoginSession")
