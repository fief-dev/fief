import functools
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any, TypeVar

from pydantic import UUID4, AnyUrl
from sqlalchemy import TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import Mapped, MappedColumn, mapped_column
from sqlalchemy.sql import func
from sqlalchemy.types import CHAR, TypeDecorator, TypeEngine


class GUID(TypeDecorator):
    """Platform-independent GUID type.

    Uses PostgreSQL's UUID type, otherwise uses
    CHAR(36), storing as regular strings.
    """

    class UUIDChar(CHAR):
        python_type = UUID4

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
    id: Mapped[UUID4] = mapped_column(GUID, primary_key=True, default=uuid.uuid4)


def now_utc():
    return datetime.now(UTC)


class TIMESTAMPAware(TypeDecorator):
    """
    MySQL and SQLite will always return naive-Python datetimes.

    We store everything as UTC, but we want to have
    only offset-aware Python datetimes, even with MySQL and SQLite.
    """

    impl = TIMESTAMP
    cache_ok = True

    def process_result_value(self, value: datetime | None, dialect):
        if value is not None and dialect.name != "postgresql":
            return value.replace(tzinfo=UTC)
        return value


class CreatedUpdatedAt(BaseModel):
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMPAware(timezone=True),
        nullable=False,
        index=True,
        default=now_utc,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMPAware(timezone=True),
        nullable=False,
        index=True,
        default=now_utc,
        server_default=func.now(),
        onupdate=now_utc,
    )


def _get_default_expires_at(timedelta_seconds: int) -> datetime:
    return datetime.now(UTC) + timedelta(seconds=timedelta_seconds)


class ExpiresAt(BaseModel):
    @declared_attr
    def expires_at(cls) -> MappedColumn[TIMESTAMPAware]:
        try:
            default_lifetime_seconds = getattr(
                cls,
                "__lifetime_seconds__",
            )
            default = functools.partial(
                _get_default_expires_at, timedelta_seconds=default_lifetime_seconds
            )
        except AttributeError:
            default = None
        return mapped_column(
            TIMESTAMPAware(timezone=True), nullable=False, index=True, default=default
        )


def PydanticUrlString(
    sa_type: TypeEngine[Any] | type[TypeEngine[Any]],
) -> type[TypeDecorator]:
    """
    Returns an SQLAlchemy type decorator that automatically converts
    `AnyUrl` objects coming from Pydantic to a proper string.
    """

    class _PydanticUrlString(TypeDecorator[str | AnyUrl]):
        impl = sa_type
        cache_ok = True

        def process_bind_param(self, value: str | AnyUrl | None, dialect):
            if isinstance(value, AnyUrl):
                return str(value)
            return value

    return _PydanticUrlString


M = TypeVar("M", bound=BaseModel)
M_UUID = TypeVar("M_UUID", bound=UUIDModel)
M_EXPIRES_AT = TypeVar("M_EXPIRES_AT", bound=ExpiresAt)
