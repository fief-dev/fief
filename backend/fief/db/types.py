from enum import Enum
from typing import Dict


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
