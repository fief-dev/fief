from typing import Optional

from fastapi import Depends, HTTPException, status

from fief.dependencies.admin_api_key import get_optional_admin_api_key
from fief.dependencies.admin_session import get_optional_admin_session_token
from fief.dependencies.current_workspace import get_current_workspace
from fief.dependencies.main_managers import get_workspace_user_manager
from fief.managers.workspace_user import WorkspaceUserManager
from fief.models import AdminAPIKey, AdminSessionToken, Workspace


async def is_authenticated_admin(
    session_token: Optional[AdminSessionToken] = Depends(
        get_optional_admin_session_token
    ),
    admin_api_key: Optional[AdminAPIKey] = Depends(get_optional_admin_api_key),
    current_workspace: Workspace = Depends(get_current_workspace),
    workspace_user_manager: WorkspaceUserManager = Depends(get_workspace_user_manager),
):
    if session_token is None and admin_api_key is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    if session_token is not None:
        workspace_user = await workspace_user_manager.get_by_workspace_and_user(
            current_workspace.id, session_token.user_id
        )
        if workspace_user is None:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    elif admin_api_key is not None:
        if admin_api_key.workspace_id != current_workspace.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
