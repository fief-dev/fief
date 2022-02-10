import uuid
from datetime import datetime, timezone
from typing import TypeVar

from pydantic import UUID4
from sqlalchemy import TIMESTAMP, Column
from sqlalchemy.dialects.postgresql import UUID
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


class UUIDModel(BaseModel):
    id: UUID4 = Column(GUID, primary_key=True, default=uuid.uuid4)  # type: ignore


def now_utc():
    return datetime.now(timezone.utc)


class CreatedUpdatedAt(BaseModel):
    created_at: datetime = Column(  # type: ignore
        TIMESTAMP(timezone=True),
        nullable=False,
        index=True,
        default=now_utc,
        server_default=func.now(),
    )
    updated_at: datetime = Column(  # type: ignore
        TIMESTAMP(timezone=True),
        nullable=False,
        index=True,
        default=now_utc,
        server_default=func.now(),
        onupdate=now_utc,
    )


M = TypeVar("M", bound=BaseModel)
M_UUID = TypeVar("M_UUID", bound=UUIDModel)
