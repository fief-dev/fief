import uuid
from typing import Any, Mapping

from fastapi_users.password import get_password_hash

from fief.models import M, Tenant, User

tenants: Mapping[str, Tenant] = {
    "default": Tenant(name="Default", default=True),
}

users: Mapping[str, User] = {
    "regular": User(
        id=uuid.uuid4(),
        email="anne@bretagne.duchy",
        hashed_password=get_password_hash("hermine"),
        tenant=tenants["default"],
    )
}

data_mapping: Mapping[str, Mapping[str, Any]] = {
    "tenants": tenants,
    "users": users,
}

__all__ = ["data_mapping"]
