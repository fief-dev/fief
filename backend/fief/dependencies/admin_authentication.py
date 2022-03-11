from typing import Optional

from fastapi import Depends, HTTPException, status

from fief.dependencies.admin_api_key import get_optional_admin_api_key
from fief.dependencies.admin_session import get_optional_admin_session_token
from fief.dependencies.current_account import get_current_account
from fief.dependencies.global_managers import get_account_user_manager
from fief.managers.account_user import AccountUserManager
from fief.models import Account, AdminAPIKey, AdminSessionToken


async def is_authenticated_admin(
    session_token: Optional[AdminSessionToken] = Depends(
        get_optional_admin_session_token
    ),
    admin_api_key: Optional[AdminAPIKey] = Depends(get_optional_admin_api_key),
    current_account: Account = Depends(get_current_account),
    account_user_manager: AccountUserManager = Depends(get_account_user_manager),
):
    if session_token is None and admin_api_key is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    if session_token is not None:
        account_user = await account_user_manager.get_by_account_and_user(
            current_account.id, session_token.user_id
        )
        if account_user is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    elif admin_api_key is not None:
        if admin_api_key.account_id != current_account.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
