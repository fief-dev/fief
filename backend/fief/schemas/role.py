from typing import List, Optional

from pydantic import UUID4

from fief.schemas.generics import BaseModel, CreatedUpdatedAt, UUIDSchema
from fief.schemas.permission import PermissionEmbedded


class RoleCreate(BaseModel):
    name: str
    granted_by_default: bool
    permissions: List[UUID4]


class RoleUpdate(BaseModel):
    name: Optional[str]
    granted_by_default: Optional[bool]
    permissions: Optional[List[UUID4]]


class BaseRole(UUIDSchema, CreatedUpdatedAt):
    name: str
    granted_by_default: bool


class Role(BaseRole):
    permissions: List[PermissionEmbedded]


class RoleEmbedded(BaseRole):
    pass
