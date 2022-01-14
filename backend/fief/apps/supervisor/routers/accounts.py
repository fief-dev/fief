from fastapi import APIRouter, Depends, status

from fief.dependencies.account_db import get_account_db
from fief.dependencies.global_managers import get_account_manager
from fief.managers import AccountManager
from fief.models import Account
from fief.schemas.account import AccountCreate, AccountRead
from fief.services.account_db import AccountDatabase

router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=AccountRead)
async def create_account(
    account_create: AccountCreate,
    manager: AccountManager = Depends(get_account_manager),
    account_db: AccountDatabase = Depends(get_account_db),
) -> Account:
    account = Account(**account_create.dict())
    account = await manager.create(account)

    account_db.migrate(account)

    return account
