from typing import Any, Optional

from pydantic import BaseModel
from pydantic.fields import Field


class AuthorizeError(BaseModel):
    error: str = Field(..., regex="invalid_redirect_uri|invalid_client")
    error_description: Optional[Any] = None
    error_uri: Optional[str] = None

    @classmethod
    def get_invalid_redirect_uri(cls, error_description: Optional[Any] = None):
        return cls(error="invalid_redirect_uri", error_description=error_description)

    @classmethod
    def get_invalid_client(cls, error_description: Optional[Any] = None):
        return cls(error="invalid_client", error_description=error_description)


class AuthorizeRedirectError(BaseModel):
    error: str = Field(
        ...,
        regex="invalid_request|unauthorized_client|access_denied|unsupported_response_type|invalid_scope|server_error|temporarily_unavailable|interaction_required|login_required|account_selection_required|consent_required|invalid_request_uri|invalid_request_object|request_not_supported|request_uri_not_supported|registration_not_supported",
    )
    error_description: Optional[Any] = None
    error_uri: Optional[str] = None

    @classmethod
    def get_invalid_request(cls, error_description: Optional[Any] = None):
        return cls(error="invalid_request", error_description=error_description)

    @classmethod
    def get_invalid_scope(cls, error_description: Optional[Any] = None):
        return cls(error="invalid_scope", error_description=error_description)

    @classmethod
    def get_login_required(cls, error_description: Optional[Any] = None):
        return cls(error="login_required", error_description=error_description)

    @classmethod
    def get_consent_required(cls, error_description: Optional[Any] = None):
        return cls(error="consent_required", error_description=error_description)

    @classmethod
    def get_request_not_supported(cls, error_description: Optional[Any] = None):
        return cls(error="request_not_supported", error_description=error_description)


class LoginError(BaseModel):
    error: str = Field(..., regex="invalid_session")
    error_description: Optional[Any] = None
    error_uri: Optional[str] = None

    @classmethod
    def get_invalid_session(cls, error_description: Optional[Any] = None):
        return cls(error="invalid_session", error_description=error_description)


class TokenResponse(BaseModel):
    access_token: str
    id_token: str
    token_type: str = Field("bearer", regex="bearer")
    expires_in: int
    refresh_token: Optional[str] = None


class TokenError(BaseModel):
    error: str = Field(
        ...,
        regex="invalid_request|invalid_client|invalid_grant|unauthorized_client|unsupported_grant_type|invalid_scope",
    )
    error_description: Optional[Any] = None
    error_uri: Optional[str] = None

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
    error: str = Field(..., regex="invalid_request")
    error_description: Optional[Any] = None
    error_uri: Optional[str] = None

    @classmethod
    def get_invalid_request(cls, error_description: Optional[Any] = None):
        return cls(error="invalid_request", error_description=error_description)
