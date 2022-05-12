from datetime import date, datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, List, Mapping, Optional, Type, TypedDict

from pydantic import constr
from sqlalchemy import JSON, Column
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import String
from sqlalchemy.orm import relationship

from fief.models.base import WorkspaceBase
from fief.models.generics import CreatedUpdatedAt, UUIDModel
from fief.schemas.generics import Address, Locale, PhoneNumber, Timezone

if TYPE_CHECKING:
    from fief.models.user_field_value import UserFieldValue


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


class UserFieldConfiguration(TypedDict):
    choices: Optional[List[str]]
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

    user_field_values: List["UserFieldValue"] = relationship(
        "UserFieldValue", back_populates="user_field", cascade="all, delete"
    )

    def get_python_type(self) -> Type[Any]:
        return USER_FIELD_TYPE_MAP[self.type]

    def get_required(self) -> bool:
        return self.configuration["required"]

    def get_default(self) -> Optional[Any]:
        return self.configuration["default"]
