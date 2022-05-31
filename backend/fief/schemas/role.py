from typing import List, Optional

from pydantic import UUID4, BaseModel

from fief.schemas.generics import CreatedUpdatedAt, UUIDSchema
from fief.schemas.permission import Permission


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
    permissions: List[Permission]


class RoleEmbedded(BaseRole):
    pass
