from fastapi import Depends, HTTPException, Request, status

from fief.dependencies.admin_api_key import get_optional_admin_api_key
from fief.dependencies.admin_session import get_admin_session_token
from fief.dependencies.current_workspace import get_current_workspace
from fief.dependencies.main_repositories import get_main_repository
from fief.models import AdminAPIKey, AdminSessionToken, Workspace
from fief.repositories import WorkspaceRepository, WorkspaceUserRepository


async def is_authenticated_admin_session(
    request: Request,
    session_token: AdminSessionToken = Depends(get_admin_session_token),
    current_workspace: Workspace = Depends(get_current_workspace),
    workspace_user_repository: WorkspaceUserRepository = Depends(
        get_main_repository(WorkspaceUserRepository)
    ),
    workspace_repository: WorkspaceRepository = Depends(
        get_main_repository(WorkspaceRepository)
    ),
):
    workspace_user = await workspace_user_repository.get_by_workspace_and_user(
        current_workspace.id, session_token.user_id
    )
    if workspace_user is None:
        admin_user_workspaces = await workspace_repository.get_by_admin_user(
            session_token.user_id
        )
        if len(admin_user_workspaces) == 0:
            raise HTTPException(
                status_code=status.HTTP_307_TEMPORARY_REDIRECT,
                headers={
                    "Location": str(request.url_for("dashboard.workspaces:create"))
                },
            )
        else:
            workspace = admin_user_workspaces[0]
            redirection = f"{request.url.scheme}://{workspace.domain}/admin/"
            raise HTTPException(
                status_code=status.HTTP_307_TEMPORARY_REDIRECT,
                headers={"Location": redirection},
            )

    request.state.user_id = str(session_token.user_id)


async def is_authenticated_admin_api(
    admin_api_key: AdminAPIKey | None = Depends(get_optional_admin_api_key),
    current_workspace: Workspace = Depends(get_current_workspace),
):
    if admin_api_key is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    if admin_api_key.workspace_id != current_workspace.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
