from fastapi import Depends

from fief.db import AsyncSession
from fief.dependencies.account import get_current_account_session
from fief.managers import TenantManager, get_manager


async def get_tenant_manager(
    session: AsyncSession = Depends(get_current_account_session),
) -> TenantManager:
    return get_manager(TenantManager, session)
