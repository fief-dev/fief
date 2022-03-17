import contextlib
from typing import TYPE_CHECKING, AsyncGenerator, Dict, Optional

from sqlalchemy import engine
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine, AsyncSession

from fief.db.engine import create_engine

if TYPE_CHECKING:
    from fief.models import Account


class AccountEngineManager:
    def __init__(self) -> None:
        self.engines: Dict[str, AsyncEngine] = {}

    def get_engine(self, database_url: engine.URL) -> AsyncEngine:
        key = str(database_url)
        try:
            return self.engines[key]
        except KeyError:
            engine = create_engine(database_url)
            self.engines[key] = engine
            return engine

    async def close_all(self):
        for engine in self.engines.values():
            await engine.dispose()


account_engine_manager = AccountEngineManager()


@contextlib.asynccontextmanager
async def get_connection(
    engine: AsyncEngine, schema_name: Optional[str] = None
) -> AsyncGenerator[AsyncConnection, None]:
    dialect_name = engine.dialect.name
    options = {}
    if dialect_name != "sqlite":
        options["schema_translate_map"] = {None: schema_name}
    async with engine.connect() as connection:
        yield await connection.execution_options(**options)


@contextlib.asynccontextmanager
async def get_account_session(account: "Account") -> AsyncGenerator[AsyncSession, None]:
    engine = account_engine_manager.get_engine(account.get_database_url())
    async with get_connection(engine, account.get_schema_name()) as connection:
        async with AsyncSession(bind=connection, expire_on_commit=False) as session:
            yield session
