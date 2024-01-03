from pydantic import UUID4
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.sqltypes import String

from fief.models.base import Base
from fief.models.generics import GUID, CreatedUpdatedAt, ExpiresAt, UUIDModel
from fief.models.user import User
from fief.settings import settings


class EmailVerification(UUIDModel, CreatedUpdatedAt, ExpiresAt, Base):
    __tablename__ = "email_verifications"
    __lifetime_seconds__ = settings.email_verification_lifetime_seconds

    code: Mapped[str] = mapped_column(
        String(length=255), nullable=False, index=True, unique=True
    )
    email: Mapped[str] = mapped_column(String(length=320), index=True, nullable=False)

    user_id: Mapped[UUID4] = mapped_column(
        GUID, ForeignKey(User.id, ondelete="CASCADE"), nullable=False
    )
    user: Mapped[User] = relationship("User", lazy="joined")
