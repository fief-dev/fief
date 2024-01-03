import secrets
from enum import StrEnum

from pydantic import UUID4
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.sqltypes import String

from fief.models.base import Base
from fief.models.generics import GUID, CreatedUpdatedAt, ExpiresAt, UUIDModel
from fief.models.oauth_account import OAuthAccount
from fief.models.tenant import Tenant
from fief.settings import settings


class RegistrationSessionFlow(StrEnum):
    PASSWORD = "PASSWORD"
    OAUTH = "OAUTH"


class RegistrationSession(UUIDModel, CreatedUpdatedAt, ExpiresAt, Base):
    __tablename__ = "registration_sessions"
    __lifetime_seconds__ = settings.registration_session_lifetime_seconds

    token: Mapped[str] = mapped_column(
        String(length=255),
        default=secrets.token_urlsafe,
        nullable=False,
        index=True,
        unique=True,
    )

    flow: Mapped[RegistrationSessionFlow] = mapped_column(
        String(length=255), default=RegistrationSessionFlow.PASSWORD, nullable=False
    )

    email: Mapped[str | None] = mapped_column(String(length=320), nullable=True)

    oauth_account_id: Mapped[UUID4 | None] = mapped_column(
        GUID, ForeignKey(OAuthAccount.id, ondelete="CASCADE"), nullable=True
    )
    oauth_account: Mapped[OAuthAccount | None] = relationship(
        "OAuthAccount", lazy="joined"
    )

    tenant_id: Mapped[UUID4] = mapped_column(
        GUID, ForeignKey(Tenant.id, ondelete="CASCADE"), nullable=False
    )
    tenant: Mapped[Tenant] = relationship("Tenant")
