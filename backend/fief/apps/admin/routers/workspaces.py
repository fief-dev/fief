from fastapi import APIRouter, Depends, HTTPException, status

from fief.db.types import create_database_connection_parameters
from fief.dependencies.admin_session import get_admin_session_token
from fief.dependencies.workspace_creation import get_workspace_creation
from fief.dependencies.workspace_db import get_workspace_db
from fief.models import AdminSessionToken
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
    database_connection_parameters = create_database_connection_parameters(
        workspace_check_connection.database_type,
        asyncio=False,
        username=workspace_check_connection.database_username,
        password=workspace_check_connection.database_password,
        host=workspace_check_connection.database_host,
        port=workspace_check_connection.database_port,
        database=workspace_check_connection.database_name,
        ssl_mode=workspace_check_connection.database_ssl_mode,
    )
    valid, message = workspace_db.check_connection(database_connection_parameters)

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
