from pydantic import UUID4, AnyUrl, Field, SecretStr, validator

from fief.errors import APIErrorCode
from fief.models.client import ClientType, LOCALHOST_HOST_PATTERN
from fief.schemas.generics import BaseModel, CreatedUpdatedAt, UUIDSchema
from fief.schemas.tenant import TenantEmbedded


def validate_redirect_uri(url: AnyUrl) -> AnyUrl:
    if url.scheme == "http" and (
        url.host is None or not LOCALHOST_HOST_PATTERN.match(url.host)
    ):
        raise ValueError(APIErrorCode.CLIENT_HTTPS_REQUIRED_ON_REDIRECT_URIS.value)
    return url


class ClientCreate(BaseModel):
    name: str
    first_party: bool
    client_type: ClientType
    redirect_uris: list[AnyUrl] = Field(..., min_items=1)
    tenant_id: UUID4

    _validate_redirect_uri = validator(
        "redirect_uris", each_item=True, allow_reuse=True
    )(validate_redirect_uri)


class ClientUpdate(BaseModel):
    name: str | None
    first_party: bool | None
    client_type: ClientType | None
    redirect_uris: list[AnyUrl] | None = Field(None, min_items=1)

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
    tenant_id: UUID4


class Client(BaseClient):
    tenant: TenantEmbedded
    encrypt_jwk: SecretStr | None
