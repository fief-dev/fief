from pydantic import HttpUrl, SecretStr, model_validator
from pydantic_core import PydanticCustomError

from fief.errors import APIErrorCode
from fief.schemas.generics import BaseModel, CreatedUpdatedAt, UUIDSchema
from fief.services.oauth_provider import AvailableOAuthProvider


def validate_openid_provider(oauth_provider: "OAuthProviderCreate"):
    provider: AvailableOAuthProvider = oauth_provider.provider
    if provider == AvailableOAuthProvider.OPENID:
        openid_configuration_endpoint = oauth_provider.openid_configuration_endpoint
        if openid_configuration_endpoint is None:
            raise PydanticCustomError(
                APIErrorCode.OAUTH_PROVIDER_MISSING_OPENID_CONFIGURATION_ENDPOINT.value,
                APIErrorCode.OAUTH_PROVIDER_MISSING_OPENID_CONFIGURATION_ENDPOINT.value,
            )
    return oauth_provider


class OAuthProviderCreate(BaseModel):
    provider: AvailableOAuthProvider
    client_id: str
    client_secret: str
    scopes: list[str]
    name: str | None = None
    openid_configuration_endpoint: HttpUrl | None = None

    _validate_openid_provider = model_validator(mode="after")(validate_openid_provider)


class OAuthProviderUpdate(BaseModel):
    client_id: str | None = None
    client_secret: str | None = None
    scopes: list[str] | None = None
    name: str | None = None
    openid_configuration_endpoint: HttpUrl | None = None


class OAuthProviderUpdateProvider(OAuthProviderUpdate):
    provider: AvailableOAuthProvider

    _validate_openid_provider = model_validator(mode="after")(validate_openid_provider)


class BaseOAuthProvider(UUIDSchema, CreatedUpdatedAt):
    provider: AvailableOAuthProvider
    client_id: SecretStr
    client_secret: SecretStr
    scopes: list[str]
    name: str | None = None
    openid_configuration_endpoint: HttpUrl | None = None


class OAuthProvider(BaseOAuthProvider):
    pass


class OAuthProviderEmbedded(BaseOAuthProvider):
    pass
