from enum import Enum
from pathlib import Path
from typing import Dict, Optional

from sqlalchemy import engine


class DatabaseType(str, Enum):
    POSTGRESQL = "POSTGRESQL"
    MYSQL = "MYSQL"
    SQLITE = "SQLITE"


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
) -> engine.URL:
    url = engine.URL.create(
        drivername=get_driver(type, asyncio=asyncio),
        username=username,
        password=password,
        host=host,
        port=port,
        database=database,
    )

    dialect_name = url.get_dialect().name
    if dialect_name == "sqlite":
        name = schema if schema is not None else database
        assert name is not None
        assert path is not None
        url = url.set(database=str(path / name))

    return url
