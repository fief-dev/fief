from pydantic import BaseModel, root_validator, validator

from fief.db.types import SSL_MODES, DatabaseType
from fief.errors import APIErrorCode


def validate_all_database_settings(cls, values):
    database_type = values.get("database_type")
    required_database_settings = [
        values.get("database_host"),
        values.get("database_port"),
        values.get("database_username"),
        values.get("database_password"),
        values.get("database_name"),
    ]

    if database_type is None and not any(required_database_settings):
        return values

    if database_type is None and any(required_database_settings):
        raise ValueError(APIErrorCode.WORKSPACE_CREATE_MISSING_DATABASE_SETTINGS.value)

    database_name = values.get("database_name")
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

    return values


def validate_ssl_mode(ssl_mode, values):
    type = values.get("database_type")

    if type is not None and ssl_mode is not None:
        ssl_mode_type = SSL_MODES[type]
        try:
            ssl_mode_type(ssl_mode)
        except ValueError as e:
            raise ValueError(
                APIErrorCode.WORKSPACE_CREATE_INVALID_SSL_MODE.value
            ) from e

    return ssl_mode


class WorkspaceCreate(BaseModel):
    name: str
    database_type: DatabaseType | None = None
    database_host: str | None = None
    database_port: int | None = None
    database_username: str | None = None
    database_password: str | None = None
    database_name: str | None = None
    database_ssl_mode: str | None = None

    _validate_all_database_settings = root_validator(allow_reuse=True)(
        validate_all_database_settings
    )
    _validate_ssl_mode = validator("database_ssl_mode", allow_reuse=True)(
        validate_ssl_mode
    )
