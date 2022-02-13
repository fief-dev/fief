from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordError(BaseModel):
    error: str = Field(..., regex="missing_token|invalid_token|invalid_password")
    error_description: Optional[str] = None
    error_uri: Optional[str] = None

    @classmethod
    def get_missing_token(cls, error_description: Optional[str] = None):
        return cls(error="missing_token", error_description=error_description)

    @classmethod
    def get_invalid_token(cls, error_description: Optional[str] = None):
        return cls(error="invalid_token", error_description=error_description)

    @classmethod
    def get_invalid_password(cls, error_description: Optional[str] = None):
        return cls(error="invalid_password", error_description=error_description)


class ResetPasswordRequest(BaseModel):
    token: str
    password: str
