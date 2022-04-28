from enum import Enum
from typing import Any, List, Optional, TypedDict

from sqlalchemy import JSON, Column
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import String

from fief.models.base import WorkspaceBase
from fief.models.generics import CreatedUpdatedAt, UUIDModel


class UserFieldType(str, Enum):
    STRING = "STRING"
    INTEGER = "INTEGER"
    BOOLEAN = "BOOLEAN"
    DATE = "DATE"
    DATETIME = "DATETIME"
    CHOICE = "CHOICE"
    PHONE_NUMBER = "PHONE_NUMBER"
    ADDRESS = "ADDRESS"
    LOCALE = "LOCALE"
    TIMEZONE = "TIMEZONE"


class UserFieldConfiguration(TypedDict):
    choices: Optional[List[str]]
    multiple: bool
    at_registration: bool
    required: bool
    editable: bool
    default: Optional[Any]


class UserField(UUIDModel, CreatedUpdatedAt, WorkspaceBase):
    __tablename__ = "user_fields"

    name: str = Column(String(length=320), nullable=False)
    slug: str = Column(String(length=320), index=True, nullable=False, unique=True)
    type: UserFieldType = Column(SQLEnum(UserFieldType), index=True, nullable=True)
    configuration: UserFieldConfiguration = Column(JSON, nullable=False)
