from fastapi import APIRouter, Depends, HTTPException, status

from fief.dependencies.account_creation import get_account_creation
from fief.errors import APIErrorCode
from fief.schemas.account import AccountCreate, AccountRead
from fief.services.account_creation import AccountCreation
from fief.services.account_db import AccountDatabaseConnectionError

router = APIRouter()


@router.post("/", name="accounts:create", status_code=status.HTTP_201_CREATED)
async def create_account(
    account_create: AccountCreate,
    account_creation: AccountCreation = Depends(get_account_creation),
) -> AccountRead:
    try:
        account = await account_creation.create(account_create)
    except AccountDatabaseConnectionError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=APIErrorCode.ACCOUNT_DB_CONNECTION_ERROR,
        ) from e

    return AccountRead.from_orm(account)
