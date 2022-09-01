from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import urlparse

from pydantic import (
    BaseSettings,
    DirectoryPath,
    Field,
    SecretStr,
    root_validator,
    validator,
)

from fief.crypto.encryption import is_valid_key
from fief.db.types import (
    DatabaseConnectionParameters,
    DatabaseType,
    create_database_connection_parameters,
)
from fief.services.email import EMAIL_PROVIDERS, AvailableEmailProvider, EmailProvider


class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class InvalidEncryptionKeyError(ValueError):
    pass


class Settings(BaseSettings):
    environment: Environment = Environment.DEVELOPMENT
    log_level: str = "INFO"
    unit_tests: bool = False
    sentry_dsn_server: Optional[str] = None
    sentry_dsn_worker: Optional[str] = None
    root_domain: str = "localhost:8000"
    allow_origin_regex: str = "http://.*localhost:[0-9]+"
    port: int = 8000

    secret: SecretStr
    encryption_key: bytes

    generated_jwk_size: int = 4096

    database_type: DatabaseType = DatabaseType.SQLITE
    database_url: Optional[str] = None
    database_host: Optional[str] = None
    database_port: Optional[int] = None
    database_username: Optional[str] = None
    database_password: Optional[str] = None
    database_name: Optional[str] = "fief.db"
    database_ssl_mode: Optional[str] = None
    database_location: DirectoryPath = Path.cwd()
    database_pool_recycle_seconds: int = 600
    database_pool_pre_pring: bool = False

    redis_url: str = "redis://localhost:6379"

    email_provider: AvailableEmailProvider = AvailableEmailProvider.NULL
    email_provider_params: Dict[str, Any] = Field(default_factory=dict)

    workspace_table_prefix: str = "fief_"

    csrf_check_enabled: bool = True
    csrf_cookie_name: str = "fief_csrftoken"
    csrf_cookie_secure: bool = True

    login_session_cookie_name: str = "fief_login_session"
    login_session_cookie_domain: str = ""
    login_session_cookie_secure: bool = True
    login_session_lifetime_seconds: int = 600

    session_cookie_name: str = "fief_session"
    session_cookie_domain: str = ""
    session_cookie_secure: bool = True
    session_lifetime_seconds: int = 86400 * 30

    authorization_code_lifetime_seconds: int = 600
    access_id_token_lifetime_seconds: int = 3600
    refresh_token_lifetime_seconds: int = 3600 * 24 * 30

    fief_domain: str = "localhost:8000"
    fief_client_id: str
    fief_client_secret: str
    fief_encryption_key: Optional[str] = None

    fief_admin_session_cookie_name: str = "fief_admin_session"
    fief_admin_session_cookie_domain: str = ""
    fief_admin_session_cookie_secure: bool = True

    fief_documentation_url: str = "https://docs.fief.dev"

    class Config:
        env_file = ".env"

    @root_validator(pre=True)
    def parse_database_url(cls, values):
        database_url = values.get("database_url")
        if database_url is not None:
            parsed_database_url = urlparse(database_url)
            values["database_host"] = parsed_database_url.hostname
            values["database_port"] = parsed_database_url.port
            values["database_username"] = parsed_database_url.username
            values["database_password"] = parsed_database_url.password
            values["database_name"] = parsed_database_url.path[1:]
        return values

    @validator("encryption_key", pre=True)
    def validate_encryption_key(cls, value: Optional[str]) -> Optional[bytes]:
        if value is None:
            return value

        key = value.encode("utf-8")
        if not is_valid_key(key):
            raise InvalidEncryptionKeyError()

        return key

    @validator("database_port", pre=True)
    def validate_empty_port(cls, value: Optional[str]) -> Optional[str]:
        if value is None or value == "":
            return None
        return value

    def get_database_connection_parameters(
        self, asyncio: bool = True, schema: Optional[str] = None
    ) -> DatabaseConnectionParameters:
        """
        Returns a proper database URL and connection arguments for async or not-async context.

        Some tools like Alembic still require a sync connection.
        """
        return create_database_connection_parameters(
            self.database_type,
            asyncio=asyncio,
            username=self.database_username,
            password=self.database_password,
            host=self.database_host,
            port=self.database_port,
            database=self.database_name,
            path=settings.database_location,
            schema=schema,
            ssl_mode=settings.database_ssl_mode,
        )

    def get_email_provider(self) -> EmailProvider:
        provider_class = EMAIL_PROVIDERS[self.email_provider]
        return provider_class(**self.email_provider_params)


settings = Settings()
