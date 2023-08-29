from datetime import datetime
from typing import cast

from pydantic import UUID4
from sqlalchemy import Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.sqltypes import JSON, String

from fief.models.base import WorkspaceBase, TABLE_PREFIX_PLACEHOLDER
from fief.models.client import Client
from fief.models.generics import (
    GUID,
    CreatedUpdatedAt,
    ExpiresAt,
    TIMESTAMPAware,
    UUIDModel,
)
from fief.models.user import User
from fief.services.acr import ACR


class AuthorizationCode(UUIDModel, CreatedUpdatedAt, ExpiresAt, WorkspaceBase):
    __tablename__ = "authorization_codes"

    code: Mapped[str] = mapped_column(
        String(length=255),
        nullable=False,
        index=True,
        unique=True,
    )
    c_hash: Mapped[str] = mapped_column(String(length=255), nullable=False)
    redirect_uri: Mapped[str] = mapped_column(String(length=2048), nullable=False)
    scope: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    authenticated_at: Mapped[datetime] = mapped_column(
        TIMESTAMPAware(timezone=True), nullable=False
    )
    nonce: Mapped[str | None] = mapped_column(String(length=255), nullable=True)
    acr: Mapped[ACR] = mapped_column(
        Enum(
            ACR,
            name=f"{TABLE_PREFIX_PLACEHOLDER}acr",
            values_callable=lambda x: [e.value for e in x],
        ),
        nullable=False,
        default=ACR.LEVEL_ZERO,
    )
    code_challenge: Mapped[str | None] = mapped_column(
        String(length=255), nullable=True
    )
    code_challenge_method: Mapped[str | None] = mapped_column(
        String(length=255), nullable=True
    )

    user_id: Mapped[UUID4] = mapped_column(
        GUID, ForeignKey(User.id, ondelete="CASCADE"), nullable=False
    )
    user: Mapped[User] = relationship("User")

    client_id: Mapped[UUID4] = mapped_column(
        GUID, ForeignKey(Client.id, ondelete="CASCADE"), nullable=False
    )
    client: Mapped[Client] = relationship("Client", lazy="joined")

    def get_code_challenge_tuple(self) -> tuple[str, str] | None:
        if self.code_challenge is not None:
            return (self.code_challenge, cast(str, self.code_challenge_method))
        return None
