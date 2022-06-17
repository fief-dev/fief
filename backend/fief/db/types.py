import ssl
from enum import Enum
from pathlib import Path
from typing import Dict, Optional, Tuple, Type, Union

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


def get_ssl_mode_parameters(
    drivername: str, ssl_mode: str, query: Dict[str, str], connect_args: Dict
) -> Tuple[Dict[str, str], Dict]:
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


DatabaseConnectionParameters = Tuple[engine.URL, Dict]


def create_database_connection_parameters(
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
) -> DatabaseConnectionParameters:
    drivername = get_driver(type, asyncio=asyncio)
    query: Dict[str, str] = {}
    connect_args: Dict = {}

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
