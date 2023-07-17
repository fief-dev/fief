import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, Generic, TypeVar

from pydantic import UUID4, EmailStr, Field, SecretStr
from pydantic.generics import GenericModel

from fief.schemas.generics import BaseModel, CreatedUpdatedAt
from fief.schemas.tenant import TenantEmbedded

if TYPE_CHECKING:  # pragma: no cover
    from fief.models.tenant import Tenant


class UserRead(CreatedUpdatedAt):
    id: UUID4
    email: EmailStr
    email_verified: bool
    is_active: bool

    tenant_id: UUID4
    tenant: TenantEmbedded
    fields: dict[str, Any]

    class Config:
        orm_mode = True


class UserFields(BaseModel):
    def get_value(self, field: str) -> Any:
        value = getattr(self, field)
        if isinstance(value, BaseModel):
            return value.dict()
        return value


UF = TypeVar("UF", bound=UserFields)


class UserCreate(GenericModel, Generic[UF]):
    email: EmailStr
    password: str
    fields: UF = Field(default_factory=dict, exclude=True)  # type: ignore


class UserCreateAdmin(UserCreate[UF], Generic[UF]):
    """
    Model allowing an admin to create a user, from dashboard or API.

    In this context, we need to set the `tenant_id` and `email_verified` manually.
    """

    email_verified: bool
    tenant_id: UUID4


class UserChangeEmail(BaseModel):
    email: EmailStr


class UserVerifyEmail(BaseModel):
    code: SecretStr


class UserChangePassword(BaseModel):
    password: SecretStr


class UserUpdate(GenericModel, Generic[UF]):
    fields: UF | None = Field(exclude=True)


class UserUpdateAdmin(UserUpdate[UF], Generic[UF]):
    email: EmailStr | None
    email_verified: bool | None
    password: str | None


class CreateAccessToken(BaseModel):
    client_id: UUID4
    scopes: list[str]


class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str = Field("bearer", regex="bearer")
    expires_in: int


class UserEmailContext(CreatedUpdatedAt):
    id: UUID4
    email: EmailStr
    tenant_id: UUID4
    fields: dict[str, Any]

    class Config:
        orm_mode = True

    @classmethod
    def create_sample(cls, tenant: "Tenant") -> "UserEmailContext":
        return cls(
            id=uuid.uuid4(),
            email="anne@bretagne.duchy",
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            tenant_id=tenant.id,
            fields={
                "first_name": "Anne",
                "last_name": "De Bretagne",
            },
        )
