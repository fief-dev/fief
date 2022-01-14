from pydantic import BaseModel

from fief.schemas.generics import UUIDSchema


class BaseAccount(BaseModel):
    name: str
    domain: str
    database_url: str


class AccountCreate(BaseAccount):
    pass


class Account(BaseAccount, UUIDSchema):
    sign_jwk: str


class AccountRead(Account):
    pass
