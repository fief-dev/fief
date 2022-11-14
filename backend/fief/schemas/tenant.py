from typing import Optional

from fief.schemas.generics import BaseModel, CreatedUpdatedAt, UUIDSchema


class TenantCreate(BaseModel):
    name: str
    registration_allowed: bool = True


class TenantUpdate(BaseModel):
    name: Optional[str]
    registration_allowed: Optional[bool]


class BaseTenant(UUIDSchema, CreatedUpdatedAt):
    name: str
    default: bool
    slug: str
    registration_allowed: bool


class Tenant(BaseTenant):
    pass


class TenantEmbedded(BaseTenant):
    pass


class TenantEmailContext(BaseTenant):
    pass
