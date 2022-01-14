from typing import Optional

from pydantic import BaseModel

from fief.schemas.generics import UUIDSchema


class AccountCreate(BaseModel):
    name: str
    database_url: Optional[str]


class BaseAccount(UUIDSchema):
    name: str
    domain: str
    database_url: Optional[str]


class Account(BaseAccount):
    sign_jwk: str


class AccountRead(BaseAccount):
    pass
