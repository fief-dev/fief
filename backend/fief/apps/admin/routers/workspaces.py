from fastapi import APIRouter, Depends, HTTPException, status

from fief.db.types import create_database_url
from fief.dependencies.admin_session import get_admin_session_token
from fief.dependencies.pagination import PaginatedObjects
from fief.dependencies.workspace import get_paginated_workspaces
from fief.dependencies.workspace_creation import get_workspace_creation
from fief.dependencies.workspace_db import get_workspace_db
from fief.models import AdminSessionToken, Workspace
from fief.schemas.generics import PaginatedResults
from fief.schemas.workspace import (
    WorkspaceCheckConnection,
    WorkspaceCreate,
    WorkspacePublic,
)
from fief.services.workspace_creation import WorkspaceCreation
from fief.services.workspace_db import (
    WorkspaceDatabase,
    WorkspaceDatabaseConnectionError,
)

router = APIRouter()


@router.get(
    "/", name="workspaces:list", dependencies=[Depends(get_admin_session_token)]
)
async def list_workspaces(
    paginated_workspaces: PaginatedObjects[Workspace] = Depends(
        get_paginated_workspaces
    ),
) -> PaginatedResults[WorkspacePublic]:
    workspaces, count = paginated_workspaces
    return PaginatedResults(
        count=count,
        results=[WorkspacePublic.from_orm(workspace) for workspace in workspaces],
    )


@router.post(
    "/check-connection",
    name="workspaces:check_connection",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(get_admin_session_token)],
)
async def check_connection(
    workspace_check_connection: WorkspaceCheckConnection,
    workspace_db: WorkspaceDatabase = Depends(get_workspace_db),
):
    url = create_database_url(
        workspace_check_connection.database_type,
        asyncio=False,
        username=workspace_check_connection.database_username,
        password=workspace_check_connection.database_password,
        host=workspace_check_connection.database_host,
        port=workspace_check_connection.database_port,
        database=workspace_check_connection.database_name,
    )
    valid, message = workspace_db.check_connection(url)

    if not valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)


@router.post("/", name="workspaces:create", status_code=status.HTTP_201_CREATED)
async def create_workspace(
    workspace_create: WorkspaceCreate,
    workspace_creation: WorkspaceCreation = Depends(get_workspace_creation),
    admin_session_token: AdminSessionToken = Depends(get_admin_session_token),
) -> WorkspacePublic:
    try:
        workspace = await workspace_creation.create(
            workspace_create, user_id=admin_session_token.user_id
        )
    except WorkspaceDatabaseConnectionError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message,
        ) from e

    return WorkspacePublic.from_orm(workspace)
