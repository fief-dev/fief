from typing import Any, Dict, Generic, TypeVar

from fastapi_users import schemas
from pydantic import UUID4, BaseModel, Field
from pydantic.generics import GenericModel

from fief.schemas.tenant import TenantEmbedded


class UserRead(schemas.BaseUser):
    tenant_id: UUID4
    tenant: TenantEmbedded
    fields: Dict[str, Any]

    class Config:
        orm_mode = True


class UserFields(BaseModel):
    pass


UF = TypeVar("UF", bound=UserFields)


class UserCreate(GenericModel, Generic[UF], schemas.BaseUserCreate):
    fields: UF = Field(default_factory=dict, exclude=True)


class UserCreateInternal(UserCreate[UF], Generic[UF]):
    """
    Utility model so that we can hook into the logic of UserManager.create
    and add some attributes before persisting into database.
    """

    tenant_id: UUID4


class UserUpdate(schemas.BaseUserUpdate):
    pass
