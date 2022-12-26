from enum import Enum
from typing import TYPE_CHECKING, Any, TypedDict

from sqlalchemy import JSON, Column, String
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import relationship

from fief.models.base import WorkspaceBase
from fief.models.generics import CreatedUpdatedAt, UUIDModel

if TYPE_CHECKING:
    from fief.models.user_field_value import UserFieldValue


class UserFieldNotChoice(TypeError):
    pass


class UserFieldChoiceNotExistingValue(ValueError):
    pass


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

    def get_display_name(self) -> str:
        display_names = {
            UserFieldType.STRING: "String",
            UserFieldType.INTEGER: "Integer",
            UserFieldType.BOOLEAN: "Boolean",
            UserFieldType.DATE: "Date",
            UserFieldType.DATETIME: "Date & Time",
            UserFieldType.CHOICE: "Choice",
            UserFieldType.PHONE_NUMBER: "Phone number",
            UserFieldType.ADDRESS: "Address",
            UserFieldType.TIMEZONE: "Timezone",
        }
        return display_names[self]

    @classmethod
    def get_choices(cls) -> list[tuple[str, str]]:
        return [(member.value, member.get_display_name()) for member in cls]


class UserFieldConfiguration(TypedDict):
    choices: list[tuple[str, str]] | None
    at_registration: bool
    at_update: bool
    required: bool
    default: Any | None


class UserField(UUIDModel, CreatedUpdatedAt, WorkspaceBase):
    __tablename__ = "user_fields"

    name: str = Column(String(length=320), nullable=False)
    slug: str = Column(String(length=320), index=True, nullable=False, unique=True)
    type: UserFieldType = Column(SQLEnum(UserFieldType), index=True, nullable=True)
    configuration: UserFieldConfiguration = Column(JSON, nullable=False)

    user_field_values: list["UserFieldValue"] = relationship(
        "UserFieldValue", back_populates="user_field", cascade="all, delete"
    )

    def get_required(self) -> bool:
        return self.configuration["required"]

    def get_default(self) -> Any | None:
        return self.configuration["default"]

    def get_type_display_name(self) -> str:
        return UserFieldType[self.type].get_display_name()

    def get_choice_label(self, value: str) -> str:
        if self.type != UserFieldType.CHOICE:
            raise UserFieldNotChoice()
        for (value, label) in self.configuration["choices"] or []:
            if value == value:
                return label
        raise UserFieldChoiceNotExistingValue()