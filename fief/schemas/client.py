from pydantic import UUID4, AnyUrl, Field, SecretStr, validator

from fief.errors import APIErrorCode
from fief.models.client import ClientType
from fief.schemas.generics import BaseModel, CreatedUpdatedAt, UUIDSchema
from fief.schemas.tenant import TenantEmbedded
from fief.services.localhost import is_localhost
from fief.settings import settings


def validate_redirect_uri(url: AnyUrl) -> AnyUrl:
    if (
        settings.client_redirect_uri_ssl_required
        and url.scheme == "http"
        and (url.host is None or not is_localhost(url.host))
    ):
        raise ValueError(APIErrorCode.CLIENT_HTTPS_REQUIRED_ON_REDIRECT_URIS.value)
    return url


class ClientCreate(BaseModel):
    name: str
    first_party: bool
    client_type: ClientType
    redirect_uris: list[AnyUrl] = Field(..., min_items=1)
    authorization_code_lifetime_seconds: int | None = Field(None, ge=0)
    access_id_token_lifetime_seconds: int | None = Field(None, ge=0)
    refresh_token_lifetime_seconds: int | None = Field(None, ge=0)
    tenant_id: UUID4

    _validate_redirect_uri = validator(
        "redirect_uris", each_item=True, allow_reuse=True
    )(validate_redirect_uri)


class ClientUpdate(BaseModel):
    name: str | None
    first_party: bool | None
    client_type: ClientType | None
    redirect_uris: list[AnyUrl] | None = Field(None, min_items=1)
    authorization_code_lifetime_seconds: int | None = Field(None, ge=0)
    access_id_token_lifetime_seconds: int | None = Field(None, ge=0)
    refresh_token_lifetime_seconds: int | None = Field(None, ge=0)

    _validate_redirect_uri = validator(
        "redirect_uris", each_item=True, allow_reuse=True
    )(validate_redirect_uri)


class BaseClient(UUIDSchema, CreatedUpdatedAt):
    name: str
    first_party: bool
    client_type: ClientType
    client_id: str
    client_secret: str
    redirect_uris: list[AnyUrl]
    authorization_code_lifetime_seconds: int
    access_id_token_lifetime_seconds: int
    refresh_token_lifetime_seconds: int
    tenant_id: UUID4


class Client(BaseClient):
    tenant: TenantEmbedded
    encrypt_jwk: SecretStr | None
