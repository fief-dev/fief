from typing import List, Optional

from sqlalchemy import JSON, Column, String, Text
from sqlalchemy.ext.hybrid import hybrid_property

from fief.crypto.encryption import decrypt, encrypt
from fief.models.base import WorkspaceBase
from fief.models.generics import CreatedUpdatedAt, UUIDModel
from fief.services.oauth_provider import AvailableOAuthProvider
from fief.settings import settings


class OAuthProvider(UUIDModel, CreatedUpdatedAt, WorkspaceBase):
    __tablename__ = "oauth_providers"

    provider: AvailableOAuthProvider = Column(String(length=255), nullable=False)
    _client_id: str = Column("client_id", Text, nullable=False)
    _client_secret: str = Column("client_secret", Text, nullable=False)
    scopes: List[str] = Column(JSON, nullable=False, default=list)
    name: Optional[str] = Column(String(length=255), nullable=True)
    authorize_endpoint: Optional[str] = Column(Text, nullable=True)
    access_token_endpoint: Optional[str] = Column(Text, nullable=True)
    refresh_token_endpoint: Optional[str] = Column(Text, nullable=True)
    revoke_token_endpoint: Optional[str] = Column(Text, nullable=True)

    def __init__(self, *args, **kwargs) -> None:
        client_id = kwargs.pop("client_id", None)
        if client_id is not None:
            self.client_id = client_id  # type: ignore
        client_secret = kwargs.pop("client_secret", None)
        if client_secret is not None:
            self.client_secret = client_secret  # type: ignore
        super().__init__(*args, **kwargs)

    @hybrid_property
    def client_id(self):
        return decrypt(self._client_id, settings.encryption_key)

    @client_id.setter  # type: ignore
    def client_id(self, value: str):
        self._client_id = encrypt(value, settings.encryption_key)

    @hybrid_property
    def client_secret(self):
        return decrypt(self._client_secret, settings.encryption_key)

    @client_secret.setter  # type: ignore
    def client_secret(self, value: str):
        self._client_secret = encrypt(value, settings.encryption_key)
