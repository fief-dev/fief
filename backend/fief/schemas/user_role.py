from pydantic import UUID4, BaseModel

from fief.schemas.generics import CreatedUpdatedAt, UUIDSchema
from fief.schemas.role import RoleEmbedded


class UserRoleCreate(BaseModel):
    id: UUID4


class BaseUserRole(UUIDSchema, CreatedUpdatedAt):
    user_id: UUID4
    role_id: UUID4


class UserRole(BaseUserRole):
    role: RoleEmbedded
