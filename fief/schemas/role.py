from pydantic import UUID4

from fief.schemas.generics import BaseModel, CreatedUpdatedAt, UUIDSchema
from fief.schemas.permission import PermissionEmbedded


class RoleCreate(BaseModel):
    name: str
    granted_by_default: bool
    permissions: list[UUID4]


class RoleUpdate(BaseModel):
    name: str | None
    granted_by_default: bool | None
    permissions: list[UUID4] | None


class BaseRole(UUIDSchema, CreatedUpdatedAt):
    name: str
    granted_by_default: bool


class Role(BaseRole):
    permissions: list[PermissionEmbedded]


class RoleEmbedded(BaseRole):
    pass
