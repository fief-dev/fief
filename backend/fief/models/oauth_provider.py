from typing import List, Optional

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
    scopes: List[str] = Column(JSON, nullable=False, default=list)
    name: Optional[str] = Column(String(length=255), nullable=True)
    openid_configuration_endpoint: Optional[str] = Column(Text, nullable=True)
