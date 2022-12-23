from sqlalchemy import JSON, Column, String, Text

from fief.crypto.encryption import FernetEngine, StringEncryptedType
from fief.models.base import WorkspaceBase
from fief.models.generics import CreatedUpdatedAt, UUIDModel
from fief.services.oauth_provider import AvailableOAuthProvider
from fief.settings import settings


class OAuthProvider(UUIDModel, CreatedUpdatedAt, WorkspaceBase):
    __tablename__ = "oauth_providers"

    provider: AvailableOAuthProvider = Column(String(length=255), nullable=False)

    client_id: str = Column(
        StringEncryptedType(Text, settings.encryption_key, FernetEngine), nullable=False
    )
    client_secret: str = Column(
        StringEncryptedType(Text, settings.encryption_key, FernetEngine), nullable=False
    )
    scopes: list[str] = Column(JSON, nullable=False, default=list)
    name: str | None = Column(String(length=255), nullable=True)
    openid_configuration_endpoint: str | None = Column(Text, nullable=True)

    def get_provider_display_name(self) -> str:
        return AvailableOAuthProvider[self.provider].get_display_name()

    def get_display_name(self) -> str:
        return f"{self.get_provider_display_name()}{f' ({self.name})' if self.name else ''}"
