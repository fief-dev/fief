from pydantic import UUID4, AnyHttpUrl

from fief.schemas.generics import BaseModel, CreatedUpdatedAt, UUIDSchema
from fief.schemas.oauth_provider import OAuthProviderEmbedded


class TenantCreate(BaseModel):
    name: str
    registration_allowed: bool = True
    theme_id: UUID4 | None
    logo_url: AnyHttpUrl | None
    application_url: AnyHttpUrl | None
    oauth_providers: list[UUID4] | None


class TenantUpdate(BaseModel):
    name: str | None
    registration_allowed: bool | None
    theme_id: UUID4 | None
    logo_url: AnyHttpUrl | None
    application_url: AnyHttpUrl | None
    oauth_providers: list[UUID4] | None


class BaseTenant(UUIDSchema, CreatedUpdatedAt):
    name: str
    default: bool
    slug: str
    registration_allowed: bool
    theme_id: UUID4 | None
    logo_url: AnyHttpUrl | None
    application_url: AnyHttpUrl | None


class Tenant(BaseTenant):
    oauth_providers: list[OAuthProviderEmbedded]


class TenantEmbedded(BaseTenant):
    pass


class TenantEmailContext(BaseTenant):
    pass
