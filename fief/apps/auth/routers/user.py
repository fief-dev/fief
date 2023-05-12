from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse

from fief.dependencies.users import (
    current_active_user,
    get_user_manager,
    get_user_update,
)
from fief.errors import APIErrorCode
from fief.models import User
from fief.schemas.user import UF, UserUpdate
from fief.services.user_manager import (
    InvalidPasswordError,
    UserAlreadyExistsError,
    UserManager,
)

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
    user: User = Depends(current_active_user),
    user_manager: UserManager = Depends(get_user_manager),
):
    try:
        user = await user_manager.update(user_update, user, request=request)
    except InvalidPasswordError as e:
        # Build a JSON response manually to fine-tune the response structure
        return JSONResponse(
            content={
                "detail": APIErrorCode.USER_UPDATE_INVALID_PASSWORD,
                "reason": [str(message) for message in e.messages],
            },
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    except UserAlreadyExistsError as e:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail=APIErrorCode.USER_UPDATE_EMAIL_ALREADY_EXISTS,
        ) from e
    else:
        return user.get_claims()
