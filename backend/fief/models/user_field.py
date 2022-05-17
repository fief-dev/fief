from enum import Enum
from typing import TYPE_CHECKING, Any, List, Optional, Tuple, TypedDict

from sqlalchemy import JSON, Column
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import String
from sqlalchemy.orm import relationship

from fief.models.base import WorkspaceBase
from fief.models.generics import CreatedUpdatedAt, UUIDModel

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
    TIMEZONE = "TIMEZONE"


class UserFieldConfiguration(TypedDict):
    choices: Optional[List[Tuple[str, str]]]
    at_registration: bool
    at_update: bool
    required: bool
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

    def get_required(self) -> bool:
        return self.configuration["required"]

    def get_default(self) -> Optional[Any]:
        return self.configuration["default"]
