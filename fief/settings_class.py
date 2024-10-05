from collections.abc import Sequence
from enum import StrEnum
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from pydantic import (
    DirectoryPath,
    EmailStr,
    Field,
    SecretStr,
    field_validator,
    model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict

from fief.crypto.encryption import is_valid_key
from fief.db.types import (
    DatabaseConnectionParameters,
    DatabaseType,
    create_database_connection_parameters,
)
from fief.paths import TEMPLATES_DIRECTORY
from fief.services.email import EMAIL_PROVIDERS, AvailableEmailProvider, EmailProvider


class Environment(StrEnum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class InvalidEncryptionKeyError(ValueError):
    pass


class InitialSettings(BaseSettings):
    secrets_dir: str | None = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


initial_settings = InitialSettings()


class Settings(BaseSettings):
    environment: Environment = Environment.PRODUCTION
    log_level: str = "INFO"
    sentry_dsn_server: str | None = None
    sentry_dsn_worker: str | None = None
    telemetry_enabled: bool = True
    allow_origin_regex: str = "http://.*localhost:[0-9]+"
    port: int = 8000

    secret: SecretStr
    encryption_key: bytes

    generated_jwk_size: int = 4096

    database_type: DatabaseType = DatabaseType.SQLITE
    database_url: str | None = None
    database_host: str | None = None
    database_port: int | None = None
    database_username: str | None = None
    database_password: str | None = None
    database_name: str | None = "fief.db"
    database_ssl_mode: str | None = None
    database_location: DirectoryPath = Path.cwd()
    database_pool_recycle_seconds: int = 600
    database_pool_pre_ping: bool = False
    database_table_prefix: str = "fief_"

    redis_url: str = "redis://localhost:6379"

    email_provider: AvailableEmailProvider = AvailableEmailProvider.NULL
    email_provider_params: dict[str, Any] = Field(default_factory=dict)
    default_from_email: str = "contact@fief.dev"
    default_from_name: str | None = "Fief"

    csrf_check_enabled: bool = True
    csrf_cookie_name: str = "fief_csrftoken"
    csrf_cookie_secure: bool = True

    session_data_cookie_name: str = "fief_session_data"
    session_data_cookie_domain: str = ""
    session_data_cookie_secure: bool = True
    session_data_cookie_lifetime_seconds: int | None = None

    user_locale_cookie_name: str = "fief_locale"
    user_locale_cookie_domain: str = ""
    user_locale_cookie_secure: bool = True
    user_locale_lifetime_seconds: int = 86400 * 30

    login_hint_cookie_name: str = "fief_login_hint"
    login_hint_cookie_domain: str = ""
    login_hint_cookie_secure: bool = True
    login_hint_cookie_lifetime_seconds: int = 86400 * 30

    login_session_cookie_name: str = "fief_login_session"
    login_session_cookie_domain: str = ""
    login_session_cookie_secure: bool = True
    login_session_lifetime_seconds: int = 3600

    registration_session_cookie_name: str = "fief_registration_session"
    registration_session_cookie_domain: str = ""
    registration_session_cookie_secure: bool = True
    registration_session_lifetime_seconds: int = 3600

    email_verification_code_length: int = 6
    email_verification_lifetime_seconds: int = 3600

    oauth_session_lifetime_seconds: int = 3600

    session_cookie_name: str = "fief_session"
    session_cookie_domain: str = ""
    session_cookie_secure: bool = True
    session_lifetime_seconds: int = 86400 * 30

    client_redirect_uri_ssl_required: bool = True

    default_authorization_code_lifetime_seconds: int = 600
    default_access_id_token_lifetime_seconds: int = 3600 * 24
    default_refresh_token_lifetime_seconds: int = 3600 * 24 * 30

    webhooks_max_attempts: int = 5

    fief_domain: str = "localhost:8000"
    fief_client_id: str
    fief_client_secret: str
    fief_encryption_key: str | None = None
    fief_main_user_email: EmailStr | None = None
    fief_main_user_password: SecretStr | None = None
    fief_main_admin_api_key: SecretStr | None = None

    fief_admin_session_cookie_name: str = "fief_admin_session"
    fief_admin_session_cookie_domain: str = ""
    fief_admin_session_cookie_secure: bool = True

    fief_documentation_url: str = "https://docs.fief.dev"

    password_min_length: int = 8
    password_min_score: int = Field(ge=0, le=4, default=3)

    model_config = SettingsConfigDict(
        env_file=".env", extra="ignore", secrets_dir=initial_settings.secrets_dir
    )

    @model_validator(mode="before")
    @classmethod
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

    @field_validator("encryption_key", mode="before")
    @classmethod
    def validate_encryption_key(cls, value: str | None) -> bytes | None:
        if value is None:
            return value

        key = value.encode("utf-8")
        if not is_valid_key(key):
            raise InvalidEncryptionKeyError()

        return key

    @field_validator("database_port", mode="before")
    @classmethod
    def validate_empty_port(cls, value: str | None) -> str | None:
        if value is None or value == "":
            return None
        return value

    def get_database_connection_parameters(
        self, asyncio: bool = True, schema: str | None = None
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
            path=self.database_location,
            schema=schema,
            ssl_mode=self.database_ssl_mode,
        )

    def get_email_provider(self) -> EmailProvider:
        provider_class = EMAIL_PROVIDERS[self.email_provider]
        return provider_class(**self.email_provider_params)

    def get_templates_directory(self) -> Sequence[Path]:
        return [TEMPLATES_DIRECTORY]
