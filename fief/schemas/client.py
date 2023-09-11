from typing import Annotated

from pydantic import UUID4, AfterValidator, AnyUrl, Field, SecretStr
from pydantic_core import PydanticCustomError

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
        raise PydanticCustomError(
            APIErrorCode.CLIENT_HTTPS_REQUIRED_ON_REDIRECT_URIS.value,
            APIErrorCode.CLIENT_HTTPS_REQUIRED_ON_REDIRECT_URIS.value,
        )
    return url


RedirectURI = Annotated[AnyUrl, AfterValidator(validate_redirect_uri)]


class ClientCreate(BaseModel):
    name: str
    first_party: bool
    client_type: ClientType
    redirect_uris: list[RedirectURI] = Field(..., min_length=1)
    authorization_code_lifetime_seconds: int | None = Field(None, ge=0)
    access_id_token_lifetime_seconds: int | None = Field(None, ge=0)
    refresh_token_lifetime_seconds: int | None = Field(None, ge=0)
    tenant_id: UUID4


class ClientUpdate(BaseModel):
    name: str | None = None
    first_party: bool | None = None
    client_type: ClientType | None = None
    redirect_uris: list[RedirectURI] | None = Field(None, min_length=1)
    authorization_code_lifetime_seconds: int | None = Field(None, ge=0)
    access_id_token_lifetime_seconds: int | None = Field(None, ge=0)
    refresh_token_lifetime_seconds: int | None = Field(None, ge=0)


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
