import uuid
from typing import Mapping, TypedDict

from fastapi_users.password import get_password_hash

from fief.models import Tenant, User, M

ModelMapping = Mapping[str, M]


class TestData(TypedDict):
    tenants: ModelMapping[Tenant]
    users: ModelMapping[User]


tenants: ModelMapping[Tenant] = {
    "default": Tenant(name="Default", default=True),
    "secondary": Tenant(name="Secondary", default=False),
}

users: ModelMapping[User] = {
    "regular": User(
        id=uuid.uuid4(),
        email="anne@bretagne.duchy",
        hashed_password=get_password_hash("hermine"),
        tenant=tenants["default"],
    )
}

data_mapping: TestData = {
    "tenants": tenants,
    "users": users,
}

__all__ = ["data_mapping", "TestData"]
