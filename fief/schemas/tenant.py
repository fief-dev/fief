from pydantic import UUID4

from fief.schemas.generics import BaseModel, CreatedUpdatedAt, UUIDSchema


class TenantCreate(BaseModel):
    name: str
    registration_allowed: bool = True
    theme_id: UUID4 | None


class TenantUpdate(BaseModel):
    name: str | None
    registration_allowed: bool | None
    theme_id: UUID4 | None


class BaseTenant(UUIDSchema, CreatedUpdatedAt):
    name: str
    default: bool
    slug: str
    registration_allowed: bool
    theme_id: UUID4 | None


class Tenant(BaseTenant):
    pass


class TenantEmbedded(BaseTenant):
    pass


class TenantEmailContext(BaseTenant):
    pass
