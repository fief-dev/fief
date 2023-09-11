from typing import Any

from pydantic import BaseModel, Field


class AuthorizeError(BaseModel):
    error: str = Field(..., pattern="invalid_redirect_uri|invalid_client")
    error_description: Any | None = None
    error_uri: str | None = None

    @classmethod
    def get_invalid_redirect_uri(cls, error_description: Any | None = None):
        return cls(error="invalid_redirect_uri", error_description=error_description)

    @classmethod
    def get_invalid_client(cls, error_description: Any | None = None):
        return cls(error="invalid_client", error_description=error_description)


class AuthorizeRedirectError(BaseModel):
    error: str = Field(
        ...,
        pattern="invalid_request|unauthorized_client|access_denied|unsupported_response_type|invalid_scope|server_error|temporarily_unavailable|interaction_required|login_required|account_selection_required|consent_required|invalid_request_uri|invalid_request_object|request_not_supported|request_uri_not_supported|registration_not_supported",
    )
    error_description: Any | None = None
    error_uri: str | None = None

    @classmethod
    def get_invalid_request(cls, error_description: Any | None = None):
        return cls(error="invalid_request", error_description=error_description)

    @classmethod
    def get_invalid_scope(cls, error_description: Any | None = None):
        return cls(error="invalid_scope", error_description=error_description)

    @classmethod
    def get_login_required(cls, error_description: Any | None = None):
        return cls(error="login_required", error_description=error_description)

    @classmethod
    def get_consent_required(cls, error_description: Any | None = None):
        return cls(error="consent_required", error_description=error_description)

    @classmethod
    def get_request_not_supported(cls, error_description: Any | None = None):
        return cls(error="request_not_supported", error_description=error_description)


class LoginError(BaseModel):
    error: str = Field(
        ..., pattern="missing_session|invalid_session|registration_disabled"
    )
    error_description: Any | None = None
    error_uri: str | None = None

    @classmethod
    def get_missing_session(cls, error_description: Any | None = None):
        return cls(error="missing_session", error_description=error_description)

    @classmethod
    def get_invalid_session(cls, error_description: Any | None = None):
        return cls(error="invalid_session", error_description=error_description)

    @classmethod
    def get_registration_disabled(cls, error_description: Any | None = None):
        return cls(error="registration_disabled", error_description=error_description)


class TokenResponse(BaseModel):
    access_token: str
    id_token: str
    token_type: str = Field("bearer", pattern="bearer")
    expires_in: int
    refresh_token: str | None = None


class TokenError(BaseModel):
    error: str = Field(
        ...,
        pattern="invalid_request|invalid_client|invalid_grant|unauthorized_client|unsupported_grant_type|invalid_scope",
    )
    error_description: Any | None = None
    error_uri: str | None = None

    @classmethod
    def get_invalid_request(cls):
        return cls(error="invalid_request")

    @classmethod
    def get_invalid_client(cls):
        return cls(error="invalid_client")

    @classmethod
    def get_invalid_grant(cls):
        return cls(error="invalid_grant")

    @classmethod
    def get_unsupported_grant_type(cls):
        return cls(error="unsupported_grant_type")

    @classmethod
    def get_invalid_scope(cls):
        return cls(error="invalid_scope")


class LogoutError(BaseModel):
    error: str = Field(..., pattern="invalid_request")
    error_description: Any | None = None
    error_uri: str | None = None

    @classmethod
    def get_invalid_request(cls, error_description: Any | None = None):
        return cls(error="invalid_request", error_description=error_description)
