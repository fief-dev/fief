from enum import Enum
from pathlib import Path
from typing import Dict, Optional, Type, Union

from sqlalchemy import engine


class DatabaseType(str, Enum):
    POSTGRESQL = "POSTGRESQL"
    MYSQL = "MYSQL"
    SQLITE = "SQLITE"


class PostreSQLSSLMode(str, Enum):
    DISABLE = "disable"
    ALLOW = "allow"
    PREFER = "prefer"
    REQUIRE = "require"
    VERIFY_CA = "verify-ca"
    VERIFY_FULL = "verify-full"


class MySQLSSLMode(str, Enum):
    DISABLED = "DISABLED"
    PREFERRED = "PREFERRED"
    REQUIRED = "REQUIRED"
    VERIFY_CA = "VERIFY_CA"
    VERIFY_IDENTITY = "VERIFY_IDENTITY"


SSLMode = Union[PostreSQLSSLMode, MySQLSSLMode]

SSL_MODES: Dict[DatabaseType, Type[SSLMode]] = {
    DatabaseType.POSTGRESQL: PostreSQLSSLMode,
    DatabaseType.MYSQL: MySQLSSLMode,
}

SSL_MODE_PARAMETERS: Dict[str, str] = {
    "postgresql": "sslmode",
    "postgresql+asyncpg": "ssl",
    "mysql+aiomysql": "ssl-mode",
    "mysql+pymysql": "ssl-mode",
}

SYNC_DRIVERS: Dict[DatabaseType, str] = {
    DatabaseType.POSTGRESQL: "postgresql",
    DatabaseType.MYSQL: "mysql+pymysql",
    DatabaseType.SQLITE: "sqlite",
}

ASYNC_DRIVERS: Dict[DatabaseType, str] = {
    DatabaseType.POSTGRESQL: "postgresql+asyncpg",
    DatabaseType.MYSQL: "mysql+aiomysql",
    DatabaseType.SQLITE: "sqlite+aiosqlite",
}


def get_driver(type: DatabaseType, *, asyncio: bool) -> str:
    drivers = ASYNC_DRIVERS if asyncio else SYNC_DRIVERS
    return drivers[type]


def create_database_url(
    type: DatabaseType,
    *,
    asyncio: bool,
    username: Optional[str] = None,
    password: Optional[str] = None,
    host: Optional[str] = None,
    port: Optional[int] = None,
    database: Optional[str] = None,
    path: Optional[Path] = None,
    schema: Optional[str] = None,
    ssl_mode: Optional[str] = None,
) -> engine.URL:
    drivername = get_driver(type, asyncio=asyncio)
    query: Dict[str, str] = {}

    if ssl_mode is not None:
        ssl_mode_parameter = SSL_MODE_PARAMETERS[drivername]
        query[ssl_mode_parameter] = ssl_mode

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

    return url
