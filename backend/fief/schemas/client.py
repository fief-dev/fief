from typing import List, Optional

from pydantic import UUID4, AnyUrl, BaseModel, Field, SecretStr, validator

from fief.errors import APIErrorCode
from fief.schemas.generics import CreatedUpdatedAt, UUIDSchema
from fief.schemas.tenant import TenantEmbedded


def validate_redirect_uri(url: AnyUrl) -> AnyUrl:
    if url.scheme == "http" and url.host != "localhost":
        raise ValueError(APIErrorCode.CLIENT_HTTPS_REQUIRED_ON_REDIRECT_URIS.value)
    return url


class ClientCreate(BaseModel):
    name: str
    first_party: bool
    redirect_uris: List[AnyUrl] = Field(..., min_items=1)
    tenant_id: UUID4

    _validate_redirect_uri = validator(
        "redirect_uris", each_item=True, allow_reuse=True
    )(validate_redirect_uri)


class ClientUpdate(BaseModel):
    name: Optional[str]
    first_party: Optional[bool]
    redirect_uris: Optional[List[AnyUrl]] = Field(None, min_items=1)

    _validate_redirect_uri = validator(
        "redirect_uris", each_item=True, allow_reuse=True
    )(validate_redirect_uri)


class BaseClient(UUIDSchema, CreatedUpdatedAt):
    name: str
    first_party: bool
    client_id: str
    client_secret: str
    redirect_uris: List[AnyUrl]
    tenant_id: UUID4


class Client(BaseClient):
    tenant: TenantEmbedded
    encrypt_jwk: Optional[SecretStr]
