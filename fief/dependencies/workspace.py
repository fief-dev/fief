from fastapi import Depends

from fief.dependencies.admin_session import get_admin_session_token
from fief.dependencies.main_repositories import get_main_repository
from fief.models import AdminSessionToken, Workspace
from fief.repositories import WorkspaceRepository


async def get_admin_user_workspaces(
    repository: WorkspaceRepository = Depends(get_main_repository(WorkspaceRepository)),
    admin_session_token: AdminSessionToken = Depends(get_admin_session_token),
) -> list[Workspace]:
    return await repository.get_by_admin_user(admin_session_token.user_id)
