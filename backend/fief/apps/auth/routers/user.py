from fastapi import APIRouter, Depends

from fief.fastapi_users import current_active_user
from fief.schemas.user import UserDB

router = APIRouter()


@router.get("/userinfo", name="user:userinfo.get")
async def get_userinfo(user: UserDB = Depends(current_active_user)):
    user_claims = user.get_claims()
    return user_claims


# OpenID specification requires the /userinfo endpoint
# to be available both with GET and POST methods 🤷‍♂️
# https://openid.net/specs/openid-connect-core-1_0.html#UserInfoRequest
@router.post("/userinfo", name="user:userinfo.post")
async def post_userinfo(user: UserDB = Depends(current_active_user)):
    user_claims = user.get_claims()
    return user_claims
