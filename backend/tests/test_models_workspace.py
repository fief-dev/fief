import pytest

from fief.db import AsyncSession
from fief.models import Workspace


@pytest.mark.asyncio
async def test_create_workspace(main_session: AsyncSession):
    workspace = Workspace(name="Duché de Bretagne", domain="bretagne.fief.dev")
    main_session.add(workspace)

    await main_session.commit()

    workspace_db = await main_session.get(Workspace, workspace.id)
    assert workspace_db is not None
