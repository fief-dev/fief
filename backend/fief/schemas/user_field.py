from datetime import date, datetime
from enum import Enum
from typing import Any, List, Mapping, Optional, Tuple, Type

from pydantic import BaseModel, constr

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


class UserFieldConfiguration(BaseModel):
    choices: Optional[List[Tuple[str, str]]]
    at_registration: bool
    required: bool
    editable: bool
    default: Optional[Any]


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
