from datetime import date, datetime
from typing import TYPE_CHECKING, Any

from pydantic import UUID4
from sqlalchemy import JSON, Boolean, Date, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.schema import UniqueConstraint

from fief.models.base import Base
from fief.models.generics import GUID, CreatedUpdatedAt, TIMESTAMPAware, UUIDModel
from fief.models.user import User
from fief.models.user_field import UserField, UserFieldType

if TYPE_CHECKING:
    hybrid_property = property
else:
    from sqlalchemy.ext.hybrid import hybrid_property


class UserFieldValue(UUIDModel, CreatedUpdatedAt, Base):
    __tablename__ = "user_field_values"
    __table_args__ = (UniqueConstraint("user_field_id", "user_id"),)

    value_string: Mapped[str | None] = mapped_column(Text, nullable=True)
    value_integer: Mapped[int | None] = mapped_column(Integer, nullable=True)
    value_boolean: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    value_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    value_datetime: Mapped[datetime | None] = mapped_column(
        TIMESTAMPAware(timezone=True), nullable=True
    )
    value_json: Mapped[Any | None] = mapped_column(JSON, nullable=True)

    user_id: Mapped[UUID4] = mapped_column(
        GUID, ForeignKey(User.id, ondelete="CASCADE"), nullable=False
    )
    user: Mapped[User] = relationship("User", back_populates="user_field_values")

    user_field_id: Mapped[UUID4] = mapped_column(
        GUID, ForeignKey(UserField.id, ondelete="CASCADE"), nullable=False
    )
    user_field: Mapped[UserField] = relationship(
        "UserField", back_populates="user_field_values", lazy="selectin"
    )

    def _get_field_value(self) -> str:
        user_field_type = self.user_field.type
        if user_field_type in [UserFieldType.INTEGER]:
            return "value_integer"
        elif user_field_type in [UserFieldType.BOOLEAN]:
            return "value_boolean"
        elif user_field_type in [UserFieldType.DATE]:
            return "value_date"
        elif user_field_type in [UserFieldType.DATETIME]:
            return "value_datetime"
        elif user_field_type in [UserFieldType.ADDRESS]:
            return "value_json"
        else:
            return "value_string"

    @hybrid_property
    def value(self) -> Any:
        field_value = self._get_field_value()
        return getattr(self, field_value)

    @value.setter
    def value(self, value: Any):
        field_value = self._get_field_value()
        setattr(self, field_value, value)

    def get_slug_and_value(self, *, json_serializable: bool = False) -> tuple[str, Any]:
        value = self.value
        if json_serializable and (
            isinstance(value, date) or isinstance(value, datetime)
        ):
            value = value.isoformat()
        return self.user_field.slug, value
