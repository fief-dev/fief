from typing import Optional

from pydantic import UUID4, BaseModel, SecretStr

from fief.schemas.generics import CreatedUpdatedAt, UUIDSchema
from fief.schemas.tenant import TenantEmbedded


class ClientCreate(BaseModel):
    name: str
    first_party: bool
    tenant_id: UUID4


class BaseClient(UUIDSchema, CreatedUpdatedAt):
    name: str
    first_party: bool
    client_id: str
    client_secret: str
    tenant_id: UUID4


class Client(BaseClient):
    tenant: TenantEmbedded
    encrypt_jwk: Optional[SecretStr]
