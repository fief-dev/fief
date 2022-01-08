from pydantic import SecretStr

from fief.schemas.generics import UUIDSchema


class BaseTenant(UUIDSchema):
    name: str
    default: bool


class Tenant(BaseTenant):
    client_id: SecretStr
    client_secret: SecretStr


class TenantReadPublic(BaseTenant):
    pass
