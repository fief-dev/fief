import enum
import re
import secrets
from datetime import datetime, timedelta, timezone

from jwcrypto import jwk
from pydantic import UUID4
from sqlalchemy import Boolean, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.sqltypes import JSON

from fief.crypto.jwk import load_jwk
from fief.models.base import WorkspaceBase
from fief.models.generics import GUID, CreatedUpdatedAt, UUIDModel
from fief.models.tenant import Tenant
from fief.settings import settings

LOCALHOST_HOST_PATTERN = re.compile(
    r"([^\.]+\.)?localhost(\d+)?|127\.0\.0\.1", flags=re.IGNORECASE
)


def get_default_redirect_uris() -> list[str]:
    return ["http://localhost:8000/docs/oauth2-redirect"]


class ClientType(str, enum.Enum):
    PUBLIC = "public"
    CONFIDENTIAL = "confidential"

    def get_display_name(self) -> str:
        display_names = {
            ClientType.PUBLIC: "Public",
            ClientType.CONFIDENTIAL: "Confidential",
        }
        return display_names[self]

    @classmethod
    def get_choices(cls) -> list[tuple[str, str]]:
        return [(member.value, member.get_display_name()) for member in cls]


class Client(UUIDModel, CreatedUpdatedAt, WorkspaceBase):
    __tablename__ = "clients"

    name: Mapped[str] = mapped_column(String(length=255), nullable=False)
    first_party: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    client_type: Mapped[ClientType] = mapped_column(
        Enum(ClientType, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=ClientType.CONFIDENTIAL,
        server_default=ClientType.CONFIDENTIAL,
    )
    client_id: Mapped[str] = mapped_column(
        String(length=255), default=secrets.token_urlsafe, nullable=False, index=True
    )
    client_secret: Mapped[str] = mapped_column(
        String(length=255), default=secrets.token_urlsafe, nullable=False, index=True
    )
    redirect_uris: Mapped[list[str]] = mapped_column(
        JSON, nullable=False, default=get_default_redirect_uris
    )
    encrypt_jwk: Mapped[str] = mapped_column(Text, nullable=True)

    authorization_code_lifetime_seconds: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=settings.default_authorization_code_lifetime_seconds,
    )
    access_id_token_lifetime_seconds: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=settings.default_access_id_token_lifetime_seconds,
    )
    refresh_token_lifetime_seconds: Mapped[int] = mapped_column(
        Integer, nullable=False, default=settings.default_refresh_token_lifetime_seconds
    )

    tenant_id: Mapped[UUID4] = mapped_column(
        GUID, ForeignKey(Tenant.id, ondelete="CASCADE"), nullable=False
    )
    tenant: Mapped[Tenant] = relationship("Tenant", lazy="joined")

    def __repr__(self) -> str:
        return f"Client(id={self.id}, name={self.name}, client_id={self.client_id})"

    def get_encrypt_jwk(self) -> jwk.JWK | None:
        if self.encrypt_jwk is None:
            return None
        return load_jwk(self.encrypt_jwk)

    def get_authorization_code_expires_at(self) -> datetime:
        return self._get_expires_at("authorization_code_lifetime_seconds")

    def get_access_id_token_expires_at(self) -> datetime:
        return self._get_expires_at("access_id_token_lifetime_seconds")

    def get_refresh_token_expires_at(self) -> datetime:
        return self._get_expires_at("refresh_token_lifetime_seconds")

    def _get_expires_at(self, attr: str) -> datetime:
        print(attr, getattr(self, attr))
        return datetime.now(timezone.utc) + timedelta(seconds=getattr(self, attr))
