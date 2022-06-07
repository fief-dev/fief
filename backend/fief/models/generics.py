import uuid
from datetime import datetime, timezone
from typing import Optional, TypeVar

from pydantic import UUID4
from sqlalchemy import TIMESTAMP, Column
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_mixin
from sqlalchemy.sql import func
from sqlalchemy.types import CHAR, TypeDecorator


class GUID(TypeDecorator):
    """Platform-independent GUID type.

    Uses PostgreSQL's UUID type, otherwise uses
    CHAR(36), storing as regular strings.
    """

    class UUIDChar(CHAR):
        python_type = UUID4  # type: ignore

    impl = UUIDChar
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(UUID())
        else:
            return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == "postgresql":
            return str(value)
        else:
            if not isinstance(value, uuid.UUID):
                return str(uuid.UUID(value))
            else:
                return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            if not isinstance(value, uuid.UUID):
                value = uuid.UUID(value)
            return value


class BaseModel:
    pass


@declarative_mixin
class UUIDModel(BaseModel):
    id: UUID4 = Column(GUID, primary_key=True, default=uuid.uuid4)


def now_utc():
    return datetime.now(timezone.utc)


class TIMESTAMPAware(TypeDecorator):
    """
    MySQL and SQLite will always return naive-Python datetimes.

    We store everything as UTC, but we want to have
    only offset-aware Python datetimes, even with MySQL and SQLite.
    """

    impl = TIMESTAMP
    cache_ok = True

    def process_result_value(self, value: Optional[datetime], dialect):
        if value is not None and dialect.name != "postgresql":
            return value.replace(tzinfo=timezone.utc)
        return value


@declarative_mixin
class CreatedUpdatedAt(BaseModel):
    created_at: datetime = Column(
        TIMESTAMPAware(timezone=True),
        nullable=False,
        index=True,
        default=now_utc,
        server_default=func.now(),
    )
    updated_at: datetime = Column(
        TIMESTAMPAware(timezone=True),
        nullable=False,
        index=True,
        default=now_utc,
        server_default=func.now(),
        onupdate=now_utc,
    )


M = TypeVar("M", bound=BaseModel)
M_UUID = TypeVar("M_UUID", bound=UUIDModel)
