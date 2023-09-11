from pydantic import BaseModel, model_validator

from fief.db.types import SSL_MODES, DatabaseType
from fief.errors import APIErrorCode


class WorkspaceCreate(BaseModel):
    name: str
    database_type: DatabaseType | None = None
    database_host: str | None = None
    database_port: int | None = None
    database_username: str | None = None
    database_password: str | None = None
    database_name: str | None = None
    database_ssl_mode: str | None = None

    @model_validator(mode="after")
    def validate_all_database_settings(self):
        database_type = self.database_type
        required_database_settings = [
            self.database_host,
            self.database_port,
            self.database_username,
            self.database_password,
            self.database_name,
        ]

        if database_type is None and not any(required_database_settings):
            return self

        if database_type is None and any(required_database_settings):
            raise ValueError(
                APIErrorCode.WORKSPACE_CREATE_MISSING_DATABASE_SETTINGS.value
            )

        database_name = self.database_name
        if database_type == DatabaseType.SQLITE:
            if database_name is None:
                raise ValueError(
                    APIErrorCode.WORKSPACE_CREATE_MISSING_DATABASE_SETTINGS.value
                )
        else:
            if not all(required_database_settings):
                raise ValueError(
                    APIErrorCode.WORKSPACE_CREATE_MISSING_DATABASE_SETTINGS.value
                )

        ssl_mode = self.database_ssl_mode
        if database_type is not None and ssl_mode is not None:
            ssl_mode_type = SSL_MODES[database_type]
            try:
                ssl_mode_type(ssl_mode)
            except ValueError as e:
                raise ValueError(
                    APIErrorCode.WORKSPACE_CREATE_INVALID_SSL_MODE.value
                ) from e

        return self
