from datetime import date, datetime
from enum import Enum
from typing import Any, Generic, List, Mapping, Optional, Tuple, Type, TypeVar, Union

from pydantic import BaseModel, StrictBool, StrictInt, StrictStr, constr
from pydantic.generics import GenericModel

from fief.models import UserField as UserFieldModel
from fief.models import UserFieldType
from fief.schemas.generics import (
    Address,
    CreatedUpdatedAt,
    PhoneNumber,
    Timezone,
    UUIDSchema,
)

USER_FIELD_TYPE_MAP: Mapping[UserFieldType, Type[Any]] = {
    UserFieldType.STRING: constr(min_length=1),
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


def get_user_field_pydantic_type(field: UserFieldModel) -> Type[Any]:
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


class UserFieldConfiguration(UserFieldConfigurationBase):
    choices: Optional[List[Tuple[str, str]]]
    default: Optional[Union[Timezone, StrictBool, StrictInt, StrictStr]]


class UserFieldConfigurationDefault(
    GenericModel, Generic[D], UserFieldConfigurationBase
):
    default: Optional[D]


class UserFieldConfigurationChoice(UserFieldConfigurationDefault[str]):
    choices: Optional[List[Tuple[str, str]]]


class UserFieldCreate(BaseModel):
    name: str
    slug: str
    type: UserFieldType
    configuration: UserFieldConfiguration


class UserFieldUpdate(BaseModel):
    name: Optional[str]
    slug: Optional[str]
    configuration: Optional[UserFieldConfiguration]


class BaseUserField(UUIDSchema, CreatedUpdatedAt):
    name: str
    slug: str
    type: UserFieldType
    configuration: UserFieldConfiguration


class UserField(BaseUserField):
    pass
