from enum import StrEnum
from typing import TYPE_CHECKING, Any, TypedDict

from sqlalchemy import JSON, String
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from fief.models.base import WorkspaceBase, TABLE_PREFIX_PLACEHOLDER
from fief.models.generics import CreatedUpdatedAt, UUIDModel

if TYPE_CHECKING:
    from fief.models.user_field_value import UserFieldValue


class UserFieldNotChoice(TypeError):
    pass


class UserFieldChoiceNotExistingValue(ValueError):
    pass


class UserFieldType(StrEnum):
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
    def choices(cls) -> list[tuple[str, str]]:
        return [(member.value, member.get_display_name()) for member in cls]

    @classmethod
    def coerce(cls, item):
        return cls(str(item)) if not isinstance(item, cls) else item


class UserFieldConfiguration(TypedDict):
    choices: list[tuple[str, str]] | None
    at_registration: bool
    at_update: bool
    required: bool
    default: Any | None


class UserField(UUIDModel, CreatedUpdatedAt, WorkspaceBase):
    __tablename__ = "user_fields"

    name: Mapped[str] = mapped_column(String(length=320), nullable=False)
    slug: Mapped[str] = mapped_column(
        String(length=320), index=True, nullable=False, unique=True
    )
    type: Mapped[UserFieldType] = mapped_column(
        SQLEnum(UserFieldType, name=f"{TABLE_PREFIX_PLACEHOLDER}userfieldtype"),
        index=True,
        nullable=True,
    )
    configuration: Mapped[UserFieldConfiguration] = mapped_column(JSON, nullable=False)

    user_field_values: Mapped[list["UserFieldValue"]] = relationship(
        "UserFieldValue", back_populates="user_field", cascade="all, delete"
    )

    def get_required(self) -> bool:
        return self.configuration["required"]

    def get_default(self) -> Any | None:
        return self.configuration.get("default")

    def get_type_display_name(self) -> str:
        return UserFieldType[self.type].get_display_name()

    def get_choice_label(self, value: str) -> str:
        if self.type != UserFieldType.CHOICE:
            raise UserFieldNotChoice()
        for value, label in self.configuration["choices"] or []:
            if value == value:
                return label
        raise UserFieldChoiceNotExistingValue()
