from fastapi import Depends

from fief.dependencies.account_db import get_account_db
from fief.dependencies.global_managers import get_account_manager
from fief.managers import AccountManager
from fief.services.account_creation import AccountCreation
from fief.services.account_db import AccountDatabase


async def get_account_creation(
    account_manager: AccountManager = Depends(get_account_manager),
    account_db: AccountDatabase = Depends(get_account_db),
) -> AccountCreation:
    return AccountCreation(account_manager, account_db)
