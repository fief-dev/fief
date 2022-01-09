from typing import List, Literal, Optional

from pydantic import BaseModel, validator

from fief.schemas.tenant import TenantReadPublic


class AuthorizationParameters(BaseModel):
    response_type: Literal["code"]
    client_id: str
    redirect_uri: str
    scope: Optional[List[str]]
    state: Optional[str]

    @validator("scope", pre=True)
    def parse_scope(cls, value: Optional[str]) -> Optional[List[str]]:
        if value is not None and not isinstance(value, list):
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
