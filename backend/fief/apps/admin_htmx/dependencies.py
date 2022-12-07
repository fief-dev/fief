from typing import TypedDict

from fastapi import Depends, Header, Request
from fief_client import FiefUserInfo

from fief.dependencies.admin_session import get_userinfo


async def get_layout(hx_boosted: bool = Header(False)) -> str:
    if hx_boosted:
        return "layout_boost.html"
    return "layout.html"


class BaseContext(TypedDict):
    request: Request
    layout: str
    user: FiefUserInfo


async def get_base_context(
    request: Request,
    layout: str = Depends(get_layout),
    userinfo: FiefUserInfo = Depends(get_userinfo),
) -> BaseContext:
    return {
        "request": request,
        "layout": layout,
        "user": userinfo,
    }
