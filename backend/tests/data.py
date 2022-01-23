import uuid
from typing import Mapping, TypedDict

from fastapi_users.password import get_password_hash

from fief.models import AuthorizationCode, Client, M, Tenant, User

ModelMapping = Mapping[str, M]


class TestData(TypedDict):
    __test__ = False

    tenants: ModelMapping[Tenant]
    clients: ModelMapping[Client]
    users: ModelMapping[User]
    authorization_codes: ModelMapping[AuthorizationCode]


tenants: ModelMapping[Tenant] = {
    "default": Tenant(name="Default", slug="default", default=True),
    "secondary": Tenant(name="Secondary", slug="secondary", default=False),
}

clients: ModelMapping[Client] = {
    "default_tenant": Client(name="Default", tenant=tenants["default"]),
    "secondary_tenant": Client(name="Secondary", tenant=tenants["secondary"]),
}

users: ModelMapping[User] = {
    "regular": User(
        id=uuid.uuid4(),
        email="anne@bretagne.duchy",
        hashed_password=get_password_hash("hermine"),
        tenant=tenants["default"],
    ),
    "regular_secondary": User(
        id=uuid.uuid4(),
        email="anne@nantes.city",
        hashed_password=get_password_hash("hermine"),
        tenant=tenants["secondary"],
    ),
}

authorization_codes: ModelMapping[AuthorizationCode] = {
    "default_regular": AuthorizationCode(
        redirect_uri="https://bretagne.duchy/callback",
        user=users["regular"],
        client=clients["default_tenant"],
    )
}

data_mapping: TestData = {
    "tenants": tenants,
    "clients": clients,
    "users": users,
    "authorization_codes": authorization_codes,
}

__all__ = ["data_mapping", "TestData"]
