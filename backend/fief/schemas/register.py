from typing import Any, Optional

from pydantic import BaseModel, Field


class RegisterError(BaseModel):
    error: str = Field(..., regex="invalid_session")
    error_description: Optional[Any] = None
    error_uri: Optional[str] = None

    @classmethod
    def get_invalid_session(cls, error_description: Optional[str] = None):
        return cls(error="invalid_session", error_description=error_description)
