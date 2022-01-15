import secrets

from fastapi import APIRouter, Depends, status

from fief.crypto.jwk import generate_jwk
from fief.dependencies.account import get_current_account
from fief.dependencies.global_managers import get_account_manager
from fief.managers import AccountManager
from fief.models import Account

router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_encryption_key(
    account: Account = Depends(get_current_account),
    manager: AccountManager = Depends(get_account_manager),
):
    key = generate_jwk(secrets.token_urlsafe(), "enc")
    account.encrypt_jwk = key.export_public()
    await manager.update(account)

    return key.export(as_dict=True)
