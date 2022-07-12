from typing import Any, Dict, Optional

from pydantic import HttpUrl, SecretStr, root_validator

from fief.errors import APIErrorCode
from fief.schemas.generics import BaseModel, CreatedUpdatedAt, UUIDSchema
from fief.services.oauth_provider import AvailableOAuthProvider


def validate_custom_provider(cls, values: Dict[str, Any]):
    provider: AvailableOAuthProvider = values["provider"]
    if provider == AvailableOAuthProvider.CUSTOM:
        authorize_endpoint = values.get("authorize_endpoint")
        access_token_endpoint = values.get("access_token_endpoint")
        if authorize_endpoint is None or access_token_endpoint is None:
            raise ValueError(APIErrorCode.OAUTH_PROVIDER_MISSING_ENDPOINT.value)
    return values


class OAuthProviderCreate(BaseModel):
    provider: AvailableOAuthProvider
    client_id: str
    client_secret: str
    name: Optional[str] = None
    authorize_endpoint: Optional[HttpUrl] = None
    access_token_endpoint: Optional[HttpUrl] = None
    refresh_token_endpoint: Optional[HttpUrl] = None
    revoke_token_endpoint: Optional[HttpUrl] = None

    _validate_custom_provider = root_validator(allow_reuse=True)(
        validate_custom_provider
    )


class OAuthProviderUpdate(BaseModel):
    client_id: Optional[str]
    client_secret: Optional[str]
    name: Optional[str]
    authorize_endpoint: Optional[HttpUrl]
    access_token_endpoint: Optional[HttpUrl]
    refresh_token_endpoint: Optional[HttpUrl]
    revoke_token_endpoint: Optional[HttpUrl]


class OAuthProviderUpdateProvider(OAuthProviderUpdate):
    provider: AvailableOAuthProvider

    _validate_custom_provider = root_validator(allow_reuse=True)(
        validate_custom_provider
    )


class BaseOAuthProvider(UUIDSchema, CreatedUpdatedAt):
    provider: AvailableOAuthProvider
    client_id: SecretStr
    client_secret: SecretStr
    name: Optional[str] = None
    authorize_endpoint: Optional[HttpUrl] = None
    access_token_endpoint: Optional[HttpUrl] = None
    refresh_token_endpoint: Optional[HttpUrl] = None
    revoke_token_endpoint: Optional[HttpUrl] = None


class OAuthProvider(BaseOAuthProvider):
    pass
