from fastapi import Depends, HTTPException, status

from fief.dependencies.admin_session import get_admin_session_token
from fief.dependencies.current_account import get_current_account
from fief.dependencies.global_managers import get_account_user_manager
from fief.managers.account_user import AccountUserManager
from fief.models import Account, AccountUser, AdminSessionToken


async def get_current_account_user(
    session_token: AdminSessionToken = Depends(get_admin_session_token),
    current_account: Account = Depends(get_current_account),
    account_user_manager: AccountUserManager = Depends(get_account_user_manager),
) -> AccountUser:
    account_user = await account_user_manager.get_by_account_and_user(
        current_account.id, session_token.user_id
    )

    if account_user is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    return account_user
