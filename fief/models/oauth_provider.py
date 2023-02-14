from sqlalchemy import JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from fief.crypto.encryption import FernetEngine, StringEncryptedType
from fief.models.base import WorkspaceBase
from fief.models.generics import CreatedUpdatedAt, UUIDModel
from fief.services.oauth_provider import AvailableOAuthProvider
from fief.settings import settings


class OAuthProvider(UUIDModel, CreatedUpdatedAt, WorkspaceBase):
    __tablename__ = "oauth_providers"

    provider: Mapped[AvailableOAuthProvider] = mapped_column(
        String(length=255), nullable=False
    )

    client_id: Mapped[str] = mapped_column(
        StringEncryptedType(Text, settings.encryption_key, FernetEngine), nullable=False
    )
    client_secret: Mapped[str] = mapped_column(
        StringEncryptedType(Text, settings.encryption_key, FernetEngine), nullable=False
    )
    scopes: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    name: Mapped[str | None] = mapped_column(String(length=255), nullable=True)
    openid_configuration_endpoint: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )

    def get_provider_display_name(self) -> str:
        return AvailableOAuthProvider[self.provider].get_display_name()

    def get_display_name(self) -> str:
        return f"{self.get_provider_display_name()}{f' ({self.name})' if self.name else ''}"
