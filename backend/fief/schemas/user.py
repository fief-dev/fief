import uuid
from datetime import date, datetime, timezone
from typing import TYPE_CHECKING, Any, Generic, TypeVar

from fastapi_users import schemas
from pydantic import UUID4, Field, StrictBool, StrictInt, StrictStr
from pydantic.generics import GenericModel

from fief.schemas.generics import Address, BaseModel, CreatedUpdatedAt, Timezone
from fief.schemas.tenant import TenantEmbedded

if TYPE_CHECKING:  # pragma: no cover
    from fief.models.tenant import Tenant


class UserRead(schemas.BaseUser, CreatedUpdatedAt):
    tenant_id: UUID4
    tenant: TenantEmbedded
    fields: dict[
        str, Address | Timezone | StrictBool | StrictInt | StrictStr | datetime | date
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
    fields: UF | None = Field(exclude=True)


class UserEmailContext(schemas.BaseUser, CreatedUpdatedAt):
    tenant_id: UUID4
    fields: dict[
        str, Address | Timezone | StrictBool | StrictInt | StrictStr | datetime | date
    ]

    class Config:
        orm_mode = True

    @classmethod
    def create_sample(cls, tenant: "Tenant") -> "UserEmailContext":
        return cls(
            id=uuid.uuid4(),
            email="anne@bretagne.duchy",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            tenant_id=tenant.id,
            tenant=tenant,
            fields={
                "first_name": "Anne",
                "last_name": "De Bretagne",
            },
        )
