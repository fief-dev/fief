from typing import Optional

from fastapi_users.router import ErrorCode
from pydantic import BaseModel


class RegisterError(BaseModel):
    error: ErrorCode
    error_description: Optional[str] = None
    error_uri: Optional[str] = None

    @classmethod
    def get_user_already_exists(cls, error_description: Optional[str] = None):
        return cls(
            error=ErrorCode.REGISTER_USER_ALREADY_EXISTS,
            error_description=error_description,
        )

    @classmethod
    def get_invalid_password(cls, error_description: Optional[str] = None):
        return cls(
            error=ErrorCode.REGISTER_INVALID_PASSWORD,
            error_description=error_description,
        )
