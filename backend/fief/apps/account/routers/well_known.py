from fastapi import APIRouter
from fastapi.param_functions import Depends
from jwcrypto import jwk

from fief.dependencies.account import get_current_account
from fief.models import Account

router = APIRouter()


@router.get("/jwks.json")
async def get_jwks(account: Account = Depends(get_current_account)):
    keyset = jwk.JWKSet(keys=account.get_sign_jwk())
    return keyset.export(private_keys=False, as_dict=True)
