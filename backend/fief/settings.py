from enum import Enum

from pydantic import BaseSettings, validator


class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    environment: Environment
    unit_tests: bool = False
    database_url: str

    account_table_prefix: str = "fief_"

    class Config:
        env_file = ".env"

    @validator("database_url")
    def replace_postgres_scheme(cls, url: str) -> str:
        """
        Ensures scheme is compatible with newest version of SQLAlchemy.
        Ref: https://help.heroku.com/ZKNTJQSK/why-is-sqlalchemy-1-4-x-not-connecting-to-heroku-postgres
        """
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        return url

    def get_database_url(self, asyncio=True) -> str:
        """
        Returns a proper database URL for async or not-async context.

        Some tools like Alembic still require a sync connection.
        """
        url = self.database_url
        if asyncio:
            if url.startswith("sqlite://"):
                return url.replace("sqlite://", "sqlite+aiosqlite://", 1)
            elif url.startswith("postgresql://"):
                return url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url


settings = Settings()
