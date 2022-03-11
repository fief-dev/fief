from fastapi import Depends
from sqlalchemy import select

from fief.dependencies.admin_session import get_admin_session_token
from fief.dependencies.global_managers import get_account_manager
from fief.dependencies.pagination import (
    Ordering,
    PaginatedObjects,
    Pagination,
    get_ordering,
    get_paginated_objects,
    get_pagination,
)
from fief.managers import AccountManager
from fief.models import Account, AccountUser, AdminSessionToken


async def get_paginated_accounts(
    pagination: Pagination = Depends(get_pagination),
    ordering: Ordering = Depends(get_ordering),
    manager: AccountManager = Depends(get_account_manager),
    admin_session_token: AdminSessionToken = Depends(get_admin_session_token),
) -> PaginatedObjects[Account]:
    statement = (
        select(Account)
        .join(Account.account_users)
        .where(AccountUser.user_id == admin_session_token.user_id)
    )
    return await get_paginated_objects(statement, pagination, ordering, manager)
