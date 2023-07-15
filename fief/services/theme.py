from typing import TYPE_CHECKING

from fief.db.workspace import WorkspaceEngineManager, get_workspace_session
from fief.models import Theme
from fief.repositories import ThemeRepository

if TYPE_CHECKING:  # pragma: no cover
    from fief.models import Workspace


async def init_default_theme(repository: ThemeRepository):
    default_theme = await repository.get_default()
    if default_theme is None:
        await repository.create(Theme.build_default())


async def init_workspace_default_theme(workspace: "Workspace"):
    async with WorkspaceEngineManager() as workspace_engine_manager:
        async with get_workspace_session(
            workspace, workspace_engine_manager
        ) as session:
            repository = ThemeRepository(session)
            await init_default_theme(repository)
