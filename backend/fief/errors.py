from enum import Enum


class APIErrorCode(str, Enum):
    CSRF_CHECK_FAILED = "CSRF_CHECK_FAILED"
    CANT_DETERMINE_VALID_WORKSPACE = "CANT_DETERMINE_VALID_WORKSPACE"

    WORKSPACE_CREATE_MISSING_DATABASE_SETTINGS = (
        "WORKSPACE_CREATE_MISSING_DATABASE_SETTINGS"
    )
    WORKSPACE_DB_CONNECTION_ERROR = "WORKSPACE_DB_CONNECTION_ERROR"
    WORKSPACE_DB_OUTDATED_MIGRATION = "WORKSPACE_DB_OUTDATED_MIGRATION"

    CLIENT_CREATE_UNKNOWN_TENANT = "CLIENT_CREATE_UNKNOWN_TENANT"
    CLIENT_HTTPS_REQUIRED_ON_REDIRECT_URIS = "CLIENT_HTTPS_REQUIRED_ON_REDIRECT_URIS"

    USER_CREATE_UNKNOWN_TENANT = "USER_CREATE_UNKNOWN_TENANT"
    USER_CREATE_ALREADY_EXISTS = "USER_CREATE_ALREADY_EXISTS"
    USER_CREATE_INVALID_PASSWORD = "USER_CREATE_INVALID_PASSWORD"
