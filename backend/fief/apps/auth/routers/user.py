from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi_users.exceptions import InvalidPasswordException, UserAlreadyExists

from fief.dependencies.user_field import get_update_user_fields
from fief.dependencies.users import UserManager, get_user_manager, get_user_update
from fief.errors import APIErrorCode
from fief.fastapi_users import current_active_user
from fief.models import User
from fief.models.user_field import UserField
from fief.schemas.user import UF, UserUpdate

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


@router.patch(
    "/profile",
    name="user:profile.patch",
    openapi_extra={
        "requestBody": {
            "content": {
                "application/json": {
                    "schema": UserUpdate.schema(
                        ref_template="#/paths/~1api~1profile/patch/requestBody/content/application~1json/schema/definitions/{model}"
                    )
                }
            },
            "required": True,
        }
    },
)
async def update_profile(
    request: Request,
    user_update: UserUpdate[UF] = Depends(get_user_update),
    update_user_fields: List[UserField] = Depends(get_update_user_fields),
    user: User = Depends(current_active_user),
    user_manager: UserManager = Depends(get_user_manager),
):
    try:
        user = await user_manager.update_with_fields(
            user_update,
            user,
            user_fields=update_user_fields,
            safe=True,
            request=request,
        )
    except InvalidPasswordException as e:
        # Build a JSON response manually to fine-tune the response structure
        return JSONResponse(
            content={
                "detail": APIErrorCode.USER_UPDATE_INVALID_PASSWORD,
                "reason": e.reason,
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    except UserAlreadyExists as e:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail=APIErrorCode.USER_UPDATE_EMAIL_ALREADY_EXISTS,
        ) from e
    else:
        return user.get_claims()
