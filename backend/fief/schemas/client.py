from typing import List, Optional

from pydantic import UUID4, AnyUrl, BaseModel, Field, SecretStr, validator

from fief.errors import APIErrorCode
from fief.schemas.generics import CreatedUpdatedAt, UUIDSchema
from fief.schemas.tenant import TenantEmbedded


class ClientCreate(BaseModel):
    name: str
    first_party: bool
    redirect_uris: List[AnyUrl] = Field(..., min_items=1)
    tenant_id: UUID4

    @validator("redirect_uris", each_item=True)
    def check_http_only_on_localhost(cls, v: AnyUrl):
        if v.scheme == "http" and v.host != "localhost":
            raise ValueError(APIErrorCode.CLIENT_HTTPS_REQUIRED_ON_REDIRECT_URIS.value)
        return v


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
