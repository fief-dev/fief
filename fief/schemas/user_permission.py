from pydantic import UUID4

from fief.schemas.generics import BaseModel, CreatedUpdatedAt
from fief.schemas.permission import PermissionEmbedded
from fief.schemas.role import RoleEmbedded


class UserPermissionCreate(BaseModel):
    id: UUID4


class BaseUserPermission(CreatedUpdatedAt):
    user_id: UUID4
    permission_id: UUID4
    from_role_id: UUID4 | None = None


class UserPermission(BaseUserPermission):
    permission: PermissionEmbedded
    from_role: RoleEmbedded | None
