from typing import Any, List, Optional

from pydantic import BaseModel

from fief.models import UserFieldType
from fief.schemas.generics import CreatedUpdatedAt, UUIDSchema


class UserFieldConfiguration(BaseModel):
    choices: Optional[List[str]]
    multiple: bool
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
