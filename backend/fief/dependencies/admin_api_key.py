from typing import Optional

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from fief.dependencies.global_managers import get_admin_api_key_manager
from fief.managers import AdminAPIKeyManager
from fief.models import AdminAPIKey

bearer_scheme = HTTPBearer(auto_error=False)


async def get_optional_admin_api_key(
    authorization: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    manager: AdminAPIKeyManager = Depends(get_admin_api_key_manager),
) -> Optional[AdminAPIKey]:
    if authorization is None:
        return None
    admin_api_key = await manager.get_by_token(authorization.credentials)
    return admin_api_key
