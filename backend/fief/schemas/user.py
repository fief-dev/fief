from typing import Any, Dict

from fastapi_users import models
from pydantic import UUID4

from fief.schemas.tenant import TenantEmbedded


class User(models.BaseUser):
    tenant_id: UUID4


class UserCreate(models.BaseUserCreate):
    pass


class UserCreateInternal(UserCreate):
    """
    Utility model so that we can hook into the logic of UserManager.create
    and add some attributes before persisting into database.
    """

    tenant_id: UUID4


class UserUpdate(models.BaseUserUpdate):
    pass


class UserDB(User, models.BaseUserDB):
    tenant_id: UUID4

    def get_claims(self) -> Dict[str, Any]:
        return {
            "sub": str(self.id),
            "email": self.email,
            "tenant_id": str(self.tenant_id),
        }


class UserRead(User):
    tenant: TenantEmbedded

    class Config:
        orm_mode = True
