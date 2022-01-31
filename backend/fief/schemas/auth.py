from typing import List, Literal, Optional

from pydantic import BaseModel, validator
from pydantic.fields import Field

from fief.schemas.tenant import TenantReadPublic


class AuthorizationParameters(BaseModel):
    response_type: str = Field(..., regex="code")
    client_id: str
    redirect_uri: str
    scope: List[str]
    state: Optional[str]

    @validator("scope", pre=True)
    def parse_scope(cls, value: str) -> List[str]:
        if not isinstance(value, list):
            return value.split()
        return value


class AuthorizeResponse(BaseModel):
    parameters: AuthorizationParameters
    tenant: TenantReadPublic


class LoginRequest(AuthorizationParameters):
    username: str
    password: str


class LoginResponse(BaseModel):
    redirect_uri: str


class TokenResponse(BaseModel):
    access_token: str
    id_token: str
    token_type: str = Field("bearer", regex="bearer")
    expires_in: int
    refresh_token: Optional[str] = None


class TokenErrorResponse(BaseModel):
    error: str = Field(
        ...,
        regex="invalid_request|invalid_client|invalid_grant|unauthorized_client|unsupported_grant_type|invalid_scope",
    )
    error_description: Optional[str] = None
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
