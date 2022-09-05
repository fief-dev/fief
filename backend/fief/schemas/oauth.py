from typing import Any, Optional

from pydantic import BaseModel
from pydantic.fields import Field


class OAuthError(BaseModel):
    error: str = Field(
        ...,
        regex="invalid_provider|oauth_error|invalid_session|missing_code|access_token_error|inactive_user|user_already_exists",
    )
    error_description: Optional[Any] = None
    error_uri: Optional[str] = None

    @classmethod
    def get_invalid_provider(cls, error_description: Optional[Any] = None):
        return cls(error="invalid_provider", error_description=error_description)

    @classmethod
    def get_oauth_error(cls, error_description: Optional[Any] = None):
        return cls(error="oauth_error", error_description=error_description)

    @classmethod
    def get_invalid_session(cls, error_description: Optional[Any] = None):
        return cls(error="invalid_session", error_description=error_description)

    @classmethod
    def get_missing_code(cls, error_description: Optional[Any] = None):
        return cls(error="missing_code", error_description=error_description)

    @classmethod
    def get_access_token_error(cls, error_description: Optional[Any] = None):
        return cls(error="access_token_error", error_description=error_description)

    @classmethod
    def get_inactive_user(cls, error_description: Optional[Any] = None):
        return cls(error="inactive_user", error_description=error_description)

    @classmethod
    def get_user_already_exists(cls, error_description: Optional[Any] = None):
        return cls(error="user_already_exists", error_description=error_description)
