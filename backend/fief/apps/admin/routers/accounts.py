from fastapi import APIRouter, Depends, HTTPException, status

from fief.dependencies.account import get_paginated_accounts
from fief.dependencies.account_creation import get_account_creation
from fief.dependencies.admin_authentication import is_authenticated_admin
from fief.dependencies.admin_session import get_admin_session_token
from fief.dependencies.pagination import PaginatedObjects
from fief.errors import APIErrorCode
from fief.models import Account, AdminSessionToken
from fief.schemas.account import AccountCreate, AccountPublic
from fief.schemas.generics import PaginatedResults
from fief.services.account_creation import AccountCreation
from fief.services.account_db import AccountDatabaseConnectionError

router = APIRouter()


@router.get("/", name="accounts:list", dependencies=[Depends(get_admin_session_token)])
async def list_accounts(
    paginated_accounts: PaginatedObjects[Account] = Depends(get_paginated_accounts),
) -> PaginatedResults[AccountPublic]:
    accounts, count = paginated_accounts
    return PaginatedResults(
        count=count,
        results=[AccountPublic.from_orm(account) for account in accounts],
    )


@router.post("/", name="accounts:create", status_code=status.HTTP_201_CREATED)
async def create_account(
    account_create: AccountCreate,
    account_creation: AccountCreation = Depends(get_account_creation),
    admin_session_token: AdminSessionToken = Depends(get_admin_session_token),
) -> AccountPublic:
    try:
        account = await account_creation.create(
            account_create, user_id=admin_session_token.user_id
        )
    except AccountDatabaseConnectionError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=APIErrorCode.ACCOUNT_DB_CONNECTION_ERROR,
        ) from e

    return AccountPublic.from_orm(account)
