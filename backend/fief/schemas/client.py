from pydantic import UUID4

from fief.schemas.generics import CreatedUpdatedAt, UUIDSchema
from fief.schemas.tenant import TenantEmbedded


class BaseClient(UUIDSchema, CreatedUpdatedAt):
    name: str
    first_party: bool
    client_id: str
    client_secret: str
    tenant_id: UUID4


class Client(BaseClient):
    tenant: TenantEmbedded
