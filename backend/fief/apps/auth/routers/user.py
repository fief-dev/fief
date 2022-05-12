from fastapi import APIRouter, Depends

from fief.fastapi_users import current_active_user
from fief.models import User

router = APIRouter()


@router.get("/userinfo", name="user:userinfo.get")
async def get_userinfo(user: User = Depends(current_active_user)):
    return user.get_claims()


# OpenID specification requires the /userinfo endpoint
# to be available both with GET and POST methods 🤷‍♂️
# https://openid.net/specs/openid-connect-core-1_0.html#UserInfoRequest
@router.post("/userinfo", name="user:userinfo.post")
async def post_userinfo(user: User = Depends(current_active_user)):
    return user.get_claims()
