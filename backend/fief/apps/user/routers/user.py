from fastapi import APIRouter, Depends

from fief.fastapi_users import current_active_user
from fief.schemas.user import UserDB

router = APIRouter()


@router.get("/userinfo", name="user:userinfo")
async def get_userinfo(user: UserDB = Depends(current_active_user)):
    user_claims = user.get_claims()
    return user_claims
