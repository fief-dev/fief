import ssl
from enum import StrEnum
from pathlib import Path
from typing import Union

from sqlalchemy import engine


class DatabaseType(StrEnum):
    POSTGRESQL = "POSTGRESQL"
    MYSQL = "MYSQL"
    SQLITE = "SQLITE"

    def get_display_name(self) -> str:
        display_names = {
            DatabaseType.POSTGRESQL: "PostgreSQL",
            DatabaseType.MYSQL: "MySQL",
            DatabaseType.SQLITE: "SQLite",
        }
        return display_names[self]

    @classmethod
    def choices(cls) -> list[tuple[str, str]]:
        return [
            (member.value, member.get_display_name())
            for member in cls
            if member != DatabaseType.SQLITE
        ]

    @classmethod
    def coerce(cls, item):
        return cls(str(item)) if not isinstance(item, cls) else item


class PostreSQLSSLMode(StrEnum):
    DISABLE = "disable"
    ALLOW = "allow"
    PREFER = "prefer"
    REQUIRE = "require"
    VERIFY_CA = "verify-ca"
    VERIFY_FULL = "verify-full"

    def get_display_name(self) -> str:
        display_names = {
            PostreSQLSSLMode.DISABLE: "Disabled",
            PostreSQLSSLMode.ALLOW: "Allow",
            PostreSQLSSLMode.PREFER: "Prefer",
            PostreSQLSSLMode.REQUIRE: "Require",
            PostreSQLSSLMode.VERIFY_CA: "Verify CA",
            PostreSQLSSLMode.VERIFY_FULL: "Verify Full",
        }
        return display_names[self]

    @classmethod
    def choices(cls) -> list[tuple[str, str]]:
        return [(member.value, member.get_display_name()) for member in cls]

    @classmethod
    def coerce(cls, item):
        return cls(str(item)) if not isinstance(item, cls) else item


class MySQLSSLMode(StrEnum):
    DISABLED = "DISABLED"
    PREFERRED = "PREFERRED"
    REQUIRED = "REQUIRED"
    VERIFY_CA = "VERIFY_CA"
    VERIFY_IDENTITY = "VERIFY_IDENTITY"

    def get_display_name(self) -> str:
        display_names = {
            MySQLSSLMode.DISABLED: "Disabled",
            MySQLSSLMode.PREFERRED: "Preferred",
            MySQLSSLMode.REQUIRED: "Required",
            MySQLSSLMode.VERIFY_CA: "Verify CA",
            MySQLSSLMode.VERIFY_IDENTITY: "Verify Identity",
        }
        return display_names[self]

    @classmethod
    def choices(cls) -> list[tuple[str, str]]:
        return [(member.value, member.get_display_name()) for member in cls]

    @classmethod
    def coerce(cls, item):
        return cls(str(item)) if not isinstance(item, cls) else item


SSLMode = Union[PostreSQLSSLMode, MySQLSSLMode]

SSL_MODES: dict[DatabaseType, type[SSLMode]] = {
    DatabaseType.POSTGRESQL: PostreSQLSSLMode,
    DatabaseType.MYSQL: MySQLSSLMode,
}

UNSAFE_SSL_MODES = {
    PostreSQLSSLMode.DISABLE,
    PostreSQLSSLMode.ALLOW,
    PostreSQLSSLMode.PREFER,
    MySQLSSLMode.DISABLED,
    MySQLSSLMode.PREFERRED,
}

SYNC_DRIVERS: dict[DatabaseType, str] = {
    DatabaseType.POSTGRESQL: "postgresql",
    DatabaseType.MYSQL: "mysql+pymysql",
    DatabaseType.SQLITE: "sqlite",
}

ASYNC_DRIVERS: dict[DatabaseType, str] = {
    DatabaseType.POSTGRESQL: "postgresql+asyncpg",
    DatabaseType.MYSQL: "mysql+aiomysql",
    DatabaseType.SQLITE: "sqlite+aiosqlite",
}


def get_driver(type: DatabaseType, *, asyncio: bool) -> str:
    drivers = ASYNC_DRIVERS if asyncio else SYNC_DRIVERS
    return drivers[type]


def get_ssl_mode_parameters(
    drivername: str, ssl_mode: str, query: dict[str, str], connect_args: dict
) -> tuple[dict[str, str], dict]:
    if ssl_mode in [PostreSQLSSLMode.DISABLE, MySQLSSLMode.DISABLED]:
        return query, connect_args

    # Build a SSL context
    context = ssl.create_default_context()

    # Basic mode: no hostname check, no certificate check
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE

    # Verify CA mode, check the certificate
    if ssl_mode in [PostreSQLSSLMode.VERIFY_CA, MySQLSSLMode.VERIFY_CA]:
        context.verify_mode = ssl.CERT_REQUIRED

    # Verify full mode, check the certificate and hostname
    if ssl_mode in [PostreSQLSSLMode.VERIFY_FULL, MySQLSSLMode.VERIFY_IDENTITY]:
        context.check_hostname = True

    # PyMySQL does not support SSL context, it uses LibPQ directly so we just pass allowed query parameters
    if drivername == "postgresql":
        query["sslmode"] = ssl_mode
        query["sslrootcert"] = ssl.get_default_verify_paths().openssl_cafile
    elif drivername in ["postgresql+asyncpg", "mysql+aiomysql", "mysql+pymysql"]:
        connect_args["ssl"] = context

    return query, connect_args


DatabaseConnectionParameters = tuple[engine.URL, dict]


def create_database_connection_parameters(
    type: DatabaseType,
    *,
    asyncio: bool,
    username: str | None = None,
    password: str | None = None,
    host: str | None = None,
    port: int | None = None,
    database: str | None = None,
    path: Path | None = None,
    schema: str | None = None,
    ssl_mode: str | None = None,
) -> DatabaseConnectionParameters:
    drivername = get_driver(type, asyncio=asyncio)
    query: dict[str, str] = {}
    connect_args: dict = {}

    if ssl_mode:
        query, connect_args = get_ssl_mode_parameters(
            drivername, ssl_mode, query, connect_args
        )

    url = engine.URL.create(
        drivername=drivername,
        username=username,
        password=password,
        host=host,
        port=port,
        database=database,
        query=query,
    )

    dialect_name = url.get_dialect().name
    if dialect_name == "sqlite":
        name = schema if schema is not None else database
        assert name is not None
        assert path is not None
        url = url.set(database=str(path / name))

    return url, connect_args
