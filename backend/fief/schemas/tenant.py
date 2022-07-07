from fief.schemas.generics import BaseModel, CreatedUpdatedAt, UUIDSchema


class TenantCreate(BaseModel):
    name: str


class BaseTenant(UUIDSchema, CreatedUpdatedAt):
    name: str
    default: bool
    slug: str


class Tenant(BaseTenant):
    pass


class TenantEmbedded(BaseTenant):
    pass
