from typing import Optional

from pydantic import BaseModel

from fief.schemas.generics import CreatedUpdatedAt, UUIDSchema


class PermissionCreate(BaseModel):
    name: str
    codename: str


class PermissionUpdate(BaseModel):
    name: Optional[str]
    codename: Optional[str]


class BasePermission(UUIDSchema, CreatedUpdatedAt):
    name: str
    codename: str


class Permission(BasePermission):
    pass


class PermissionEmbedded(BasePermission):
    pass
