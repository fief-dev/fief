from collections.abc import Mapping
from datetime import date, datetime
from enum import Enum
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, StrictBool, StrictInt, StrictStr

from fief.models import UserField as UserFieldModel
from fief.models import UserFieldType
from fief.schemas.generics import (
    Address,
    CreatedUpdatedAt,
    NonEmptyString,
    PhoneNumber,
    Timezone,
    UUIDSchema,
)

USER_FIELD_TYPE_MAP: Mapping[UserFieldType, type[Any]] = {
    UserFieldType.STRING: NonEmptyString,
    UserFieldType.INTEGER: int,
    UserFieldType.BOOLEAN: bool,
    UserFieldType.DATE: date,
    UserFieldType.DATETIME: datetime,
    UserFieldType.CHOICE: str,
    UserFieldType.PHONE_NUMBER: PhoneNumber,
    UserFieldType.ADDRESS: Address,
    UserFieldType.TIMEZONE: Timezone,
}

USER_FIELD_CAN_HAVE_DEFAULT: Mapping[UserFieldType, bool] = {
    UserFieldType.STRING: True,
    UserFieldType.INTEGER: True,
    UserFieldType.BOOLEAN: True,
    UserFieldType.DATE: False,
    UserFieldType.DATETIME: False,
    UserFieldType.CHOICE: True,
    UserFieldType.PHONE_NUMBER: False,
    UserFieldType.ADDRESS: False,
    UserFieldType.TIMEZONE: True,
}

D = TypeVar("D", Timezone, bool, int, str)
UFT = TypeVar("UFT", bound=UserFieldType)


def get_user_field_pydantic_type(field: UserFieldModel) -> type[Any]:
    if field.type == UserFieldType.CHOICE:
        choices = (
            field.configuration["choices"] if field.configuration["choices"] else []
        )
        return Enum(  # type: ignore
            f"{field.slug.capitalize()}Enum",
            [(value, value) for (value, _) in choices],
            type=str,
        )

    return USER_FIELD_TYPE_MAP[field.type]


class UserFieldConfigurationBase(BaseModel):
    at_registration: bool
    required: bool
    at_update: bool


ChoiceTupleType = tuple[str, str]


class UserFieldConfiguration(UserFieldConfigurationBase):
    choices: list[ChoiceTupleType] | None = None
    default: Timezone | StrictBool | StrictInt | StrictStr | None = None


class UserFieldConfigurationDefault(UserFieldConfigurationBase, Generic[D]):
    default: D | None = None


class UserFieldConfigurationChoice(UserFieldConfigurationDefault[str]):
    choices: list[ChoiceTupleType] | None = None


class UserFieldCreate(BaseModel):
    name: str
    slug: str
    type: UserFieldType
    configuration: UserFieldConfiguration


class UserFieldUpdate(BaseModel):
    name: str | None = None
    slug: str | None = None
    configuration: UserFieldConfiguration | None = None


class BaseUserField(UUIDSchema, CreatedUpdatedAt):
    name: str
    slug: str
    type: UserFieldType
    configuration: UserFieldConfiguration


class UserField(BaseUserField):
    pass
