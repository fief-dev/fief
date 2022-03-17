from typing import AsyncGenerator

import httpx
import pytest
from fastapi import Depends, FastAPI, status
from sqlalchemy import select

from fief.db import AsyncSession
from fief.dependencies.current_workspace import (
    get_current_workspace,
    get_current_workspace_session,
)
from fief.models import Tenant, Workspace
from tests.conftest import TestClientGeneratorType


@pytest.fixture
def app() -> FastAPI:
    app = FastAPI()

    @app.get("/workspace")
    async def current_workspace(workspace: Workspace = Depends(get_current_workspace)):
        return {"id": str(workspace.id)}

    @app.get("/tenants")
    async def current_workspace_tenants(
        session: AsyncSession = Depends(get_current_workspace_session),
    ):
        statement = select(Tenant)
        results = await session.execute(statement)
        results_list = results.all()
        return {"count": len(results_list)}

    return app


@pytest.fixture
@pytest.mark.asyncio
async def test_client_auth(
    test_client_auth_generator: TestClientGeneratorType, app: FastAPI
) -> AsyncGenerator[httpx.AsyncClient, None]:
    async with test_client_auth_generator(app) as test_client:
        yield test_client


@pytest.mark.asyncio
class TestGetCurrentWorkspaceFromHostHeader:
    async def test_not_existing_workspace(self, test_client_auth: httpx.AsyncClient):
        response = await test_client_auth.get(
            "/workspace", headers={"Host": "unknown.fief.dev"}
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    async def test_existing_workspace(
        self, test_client_auth: httpx.AsyncClient, workspace: Workspace
    ):
        response = await test_client_auth.get(
            "/workspace", headers={"Host": workspace.domain}
        )

        assert response.status_code == status.HTTP_200_OK

        json = response.json()
        assert json["id"] == str(workspace.id)


@pytest.mark.asyncio
class TestGetCurrentWorkspaceSession:
    async def test_existing_workspace(
        self, test_client_auth: httpx.AsyncClient, workspace: Workspace
    ):
        response = await test_client_auth.get(
            "/tenants", headers={"Host": workspace.domain}
        )

        assert response.status_code == status.HTTP_200_OK

        json = response.json()
        assert json["count"] == 2
