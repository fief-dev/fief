from fief.schemas.generics import CreatedUpdatedAt, UUIDSchema


class BaseTenant(UUIDSchema, CreatedUpdatedAt):
    name: str
    default: bool
    slug: str


class Tenant(BaseTenant):
    pass


class TenantEmbedded(BaseTenant):
    pass
