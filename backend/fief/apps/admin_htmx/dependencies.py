from typing import TypedDict

from fastapi import Depends, Header, Request
from fief_client import FiefUserInfo

from fief.dependencies.admin_session import get_userinfo
from fief.dependencies.current_workspace import get_current_workspace
from fief.dependencies.workspace import get_admin_user_workspaces
from fief.models import Workspace


async def get_layout(hx_request: bool = Header(False)) -> str:
    if hx_request:
        return "admin/layout_boost.html"
    return "admin/layout.html"


class BaseContext(TypedDict):
    request: Request
    layout: str
    hx_target: str | None
    user: FiefUserInfo
    current_workspace: Workspace
    workspaces: list[Workspace]


async def get_base_context(
    request: Request,
    hx_target: str | None = Header(None),
    layout: str = Depends(get_layout),
    userinfo: FiefUserInfo = Depends(get_userinfo),
    current_workspace: Workspace = Depends(get_current_workspace),
    workspaces: list[Workspace] = Depends(get_admin_user_workspaces),
) -> BaseContext:
    return {
        "request": request,
        "layout": layout,
        "hx_target": hx_target,
        "user": userinfo,
        "current_workspace": current_workspace,
        "workspaces": workspaces,
    }
