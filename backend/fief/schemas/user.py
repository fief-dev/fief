from datetime import date, datetime
from typing import Any, Dict, Generic, Optional, TypeVar, Union

from fastapi_users import schemas
from pydantic import UUID4, Field, StrictBool, StrictInt, StrictStr
from pydantic.generics import GenericModel

from fief.schemas.generics import Address, BaseModel, CreatedUpdatedAt, Timezone
from fief.schemas.tenant import TenantEmbedded


class UserRead(schemas.BaseUser, CreatedUpdatedAt):
    tenant_id: UUID4
    tenant: TenantEmbedded
    fields: Dict[
        str, Union[Address, Timezone, StrictBool, StrictInt, StrictStr, datetime, date]
    ]

    class Config:
        orm_mode = True


class UserFields(BaseModel):
    def get_value(self, field: str) -> Any:
        value = getattr(self, field)
        if isinstance(value, BaseModel):
            return value.dict()
        return value


UF = TypeVar("UF", bound=UserFields)


class UserCreate(GenericModel, Generic[UF], schemas.BaseUserCreate):
    fields: UF = Field(default_factory=dict, exclude=True)


class UserCreateInternal(UserCreate[UF], Generic[UF]):
    """
    Utility model so that we can hook into the logic of UserManager.create
    and add some attributes before persisting into database.
    """

    tenant_id: UUID4


class UserUpdate(GenericModel, Generic[UF], schemas.BaseUserUpdate):
    fields: Optional[UF] = Field(exclude=True)
