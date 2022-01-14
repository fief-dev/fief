from fastapi import APIRouter, Depends, HTTPException, status

from fief.dependencies.account_db import get_account_db
from fief.dependencies.global_managers import get_account_manager
from fief.errors import ErrorCode
from fief.managers import AccountManager
from fief.models import Account
from fief.schemas.account import AccountCreate, AccountRead
from fief.services.account_db import AccountDatabase, AccountDatabaseConnectionError

router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_account(
    account_create: AccountCreate,
    manager: AccountManager = Depends(get_account_manager),
    account_db: AccountDatabase = Depends(get_account_db),
) -> AccountRead:
    account = Account(**account_create.dict())
    domain = await manager.get_available_subdomain(account.name)
    account.domain = domain

    try:
        account_db.migrate(account)
    except AccountDatabaseConnectionError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorCode.ACCOUNT_DB_CONNECTION_ERROR,
        ) from e

    account = await manager.create(account)

    return AccountRead.from_orm(account)
