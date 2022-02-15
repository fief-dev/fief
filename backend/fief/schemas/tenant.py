from fief.schemas.generics import UUIDSchema


class BaseTenant(UUIDSchema):
    name: str
    default: bool


class Tenant(BaseTenant):
    slug: str


class TenantReadPublic(BaseTenant):
    pass
