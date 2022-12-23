from fief.services.workspace_db import WorkspaceDatabase


async def get_workspace_db() -> WorkspaceDatabase:
    return WorkspaceDatabase()
