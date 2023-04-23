from collections.abc import AsyncGenerator

from fastapi import Header, HTTPException, status
from fastapi.param_functions import Depends
from posthog import Posthog

from fief.db import AsyncSession
from fief.db.workspace import WorkspaceEngineManager, get_workspace_session
from fief.dependencies.db import get_workspace_engine_manager
from fief.dependencies.main_repositories import get_main_repository
from fief.dependencies.telemetry import get_posthog
from fief.dependencies.workspace_db import get_workspace_db
from fief.errors import APIErrorCode
from fief.models import Workspace
from fief.repositories import WorkspaceRepository
from fief.services.posthog import get_workspace_properties
from fief.services.workspace_db import WorkspaceDatabase


async def get_host(
    host: str | None = Header(None, include_in_schema=False)
) -> str | None:
    return host


async def get_current_workspace(
    host: str | None = Depends(get_host),
    repository: WorkspaceRepository = Depends(get_main_repository(WorkspaceRepository)),
    workspace_db: WorkspaceDatabase = Depends(get_workspace_db),
    posthog: Posthog = Depends(get_posthog),
) -> Workspace:
    workspace = None
    if host is not None:
        workspace = await repository.get_by_domain(host)

    if workspace is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=APIErrorCode.CANT_DETERMINE_VALID_WORKSPACE,
        )

    latest_revision = workspace_db.get_latest_revision()
    if workspace.alembic_revision != latest_revision:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=APIErrorCode.WORKSPACE_DB_OUTDATED_MIGRATION,
        )

    posthog.group_identify(
        "workspace", str(workspace.id), properties=get_workspace_properties(workspace)
    )

    return workspace


async def get_current_workspace_session(
    workspace: Workspace = Depends(get_current_workspace),
    workspace_engine_manager: WorkspaceEngineManager = Depends(
        get_workspace_engine_manager
    ),
) -> AsyncGenerator[AsyncSession, None]:
    try:
        async with get_workspace_session(
            workspace, workspace_engine_manager
        ) as session:
            yield session
    except ConnectionError as e:
        import traceback

        traceback.print_exception(e)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=APIErrorCode.WORKSPACE_DB_CONNECTION_ERROR,
        ) from e
