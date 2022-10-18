from typing import Any, Dict, List, Optional

from pydantic import HttpUrl, SecretStr, root_validator

from fief.errors import APIErrorCode
from fief.schemas.generics import BaseModel, CreatedUpdatedAt, UUIDSchema
from fief.services.oauth_provider import AvailableOAuthProvider


def validate_openid_provider(cls, values: Dict[str, Any]):
    provider: AvailableOAuthProvider = values["provider"]
    if provider == AvailableOAuthProvider.OPENID:
        openid_configuration_endpoint = values.get("openid_configuration_endpoint")
        if openid_configuration_endpoint is None:
            raise ValueError(
                APIErrorCode.OAUTH_PROVIDER_MISSING_OPENID_CONFIGURATION_ENDPOINT.value
            )
    return values


class OAuthProviderCreate(BaseModel):
    provider: AvailableOAuthProvider
    client_id: str
    client_secret: str
    scopes: List[str]
    name: Optional[str] = None
    openid_configuration_endpoint: Optional[HttpUrl] = None

    _validate_openid_provider = root_validator(allow_reuse=True)(
        validate_openid_provider
    )


class OAuthProviderUpdate(BaseModel):
    client_id: Optional[str]
    client_secret: Optional[str]
    scopes: Optional[List[str]]
    name: Optional[str]
    openid_configuration_endpoint: Optional[HttpUrl]


class OAuthProviderUpdateProvider(OAuthProviderUpdate):
    provider: AvailableOAuthProvider

    _validate_openid_provider = root_validator(allow_reuse=True)(
        validate_openid_provider
    )


class BaseOAuthProvider(UUIDSchema, CreatedUpdatedAt):
    provider: AvailableOAuthProvider
    client_id: SecretStr
    client_secret: SecretStr
    scopes: List[str]
    name: Optional[str] = None
    openid_configuration_endpoint: Optional[HttpUrl] = None


class OAuthProvider(BaseOAuthProvider):
    pass
