from datetime import date, datetime
from typing import Any, List, Mapping, Optional, Type

from pydantic import BaseModel, constr

from fief.models import UserFieldType
from fief.schemas.generics import (
    Address,
    CreatedUpdatedAt,
    Locale,
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
    UserFieldType.LOCALE: Locale,
    UserFieldType.TIMEZONE: Timezone,
}


class UserFieldConfiguration(BaseModel):
    choices: Optional[List[str]]
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
