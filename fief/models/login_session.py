import secrets
from typing import cast

from pydantic import UUID4
from sqlalchemy import Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.sqltypes import JSON, String

from fief.models.base import WorkspaceBase
from fief.models.client import Client
from fief.models.generics import GUID, CreatedUpdatedAt, ExpiresAt, UUIDModel
from fief.services.acr import ACR
from fief.settings import settings


class LoginSession(UUIDModel, CreatedUpdatedAt, ExpiresAt, WorkspaceBase):
    __tablename__ = "login_sessions"
    __lifetime_seconds__ = settings.login_session_lifetime_seconds

    token: Mapped[str] = mapped_column(
        String(length=255),
        default=secrets.token_urlsafe,
        nullable=False,
        index=True,
        unique=True,
    )
    response_type: Mapped[str] = mapped_column(String(length=255), nullable=False)
    response_mode: Mapped[str] = mapped_column(String(length=255), nullable=False)
    redirect_uri: Mapped[str] = mapped_column(String(length=2048), nullable=False)
    scope: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    prompt: Mapped[str | None] = mapped_column(String(length=255), nullable=True)
    state: Mapped[str | None] = mapped_column(String(length=2048), nullable=True)
    nonce: Mapped[str | None] = mapped_column(String(length=255), nullable=True)
    acr: Mapped[ACR] = mapped_column(
        Enum(ACR, name="fief_acr", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=ACR.LEVEL_ZERO,
    )
    code_challenge: Mapped[str | None] = mapped_column(
        String(length=255), nullable=True
    )
    code_challenge_method: Mapped[str | None] = mapped_column(
        String(length=255), nullable=True
    )

    client_id: Mapped[UUID4] = mapped_column(
        GUID, ForeignKey(Client.id, ondelete="CASCADE"), nullable=False
    )
    client: Mapped[Client] = relationship("Client", lazy="joined")

    def get_code_challenge_tuple(self) -> tuple[str, str] | None:
        if self.code_challenge is not None:
            return (self.code_challenge, cast(str, self.code_challenge_method))
        return None
