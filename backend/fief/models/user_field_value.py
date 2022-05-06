from typing import Any, Tuple

from pydantic import UUID4
from sqlalchemy import JSON, Boolean, Column, Date, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import UniqueConstraint

from fief.models.base import WorkspaceBase
from fief.models.generics import GUID, CreatedUpdatedAt, TIMESTAMPAware, UUIDModel
from fief.models.user import User
from fief.models.user_field import UserField, UserFieldType


class UserFieldValue(UUIDModel, CreatedUpdatedAt, WorkspaceBase):
    __tablename__ = "user_field_values"
    __table_args__ = (UniqueConstraint("user_field_id", "user_id"),)

    value_string = Column(Text, nullable=True)
    value_integer = Column(Integer, nullable=True)
    value_boolean = Column(Boolean, nullable=True)
    value_date = Column(Date, nullable=True)
    value_datetime = Column(TIMESTAMPAware(timezone=True), nullable=True)
    value_json = Column(JSON, nullable=True)

    user_id: UUID4 = Column(GUID, ForeignKey(User.id, ondelete="CASCADE"), nullable=False)  # type: ignore
    user: User = relationship("User", back_populates="user_field_values")

    user_field_id: UUID4 = Column(GUID, ForeignKey(UserField.id, ondelete="CASCADE"), nullable=False)  # type: ignore
    user_field: UserField = relationship(
        "UserField", back_populates="user_field_values", lazy="selectin"
    )

    def get_value(self) -> Any:
        user_field_type = self.user_field.type
        if user_field_type in [
            UserFieldType.STRING,
            UserFieldType.CHOICE,
            UserFieldType.PHONE_NUMBER,
            UserFieldType.LOCALE,
            UserFieldType.TIMEZONE,
        ]:
            return self.value_string
        elif user_field_type in [UserFieldType.INTEGER]:
            return self.value_integer
        elif user_field_type in [UserFieldType.BOOLEAN]:
            return self.value_boolean
        elif user_field_type in [UserFieldType.DATE]:
            return self.value_date
        elif user_field_type in [UserFieldType.DATETIME]:
            return self.value_datetime
        elif user_field_type in [UserFieldType.ADDRESS]:
            return self.value_json

    def get_slug_and_value(self) -> Tuple[str, Any]:
        return self.user_field.slug, self.get_value()
