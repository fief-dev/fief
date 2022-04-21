from typing import AsyncGenerator, Tuple

import httpx
import pytest
from fastapi import Depends, FastAPI, status
from sqlalchemy import engine, select

from fief.db import AsyncSession
from fief.db.types import DatabaseType
from fief.dependencies.current_workspace import (
    get_current_workspace,
    get_current_workspace_session,
)
from fief.errors import APIErrorCode
from fief.models import Tenant, Workspace
from tests.types import TestClientGeneratorType


@pytest.fixture(
    scope="module",
    params=[
        {"type": "POSTGRESQL", "host": "localhost", "port": 5432},
        {"type": "POSTGRESQL", "host": "localhost", "port": 5433},
        {"type": "POSTGRESQL", "host": "db.normandy.duchy", "port": 5432},
        {"type": "MYSQL", "host": "localhost", "port": 3306},
        {"type": "MYSQL", "host": "localhost", "port": 3307},
        {"type": "MYSQL", "host": "db.normandy.duchy", "port": 3306},
    ],
    ids=[
        "POSTGRESQL Invalid credentials",
        "POSTGRESQL Invalid port",
        "POSTGRESQL Invalid host",
        "MYSQL Invalid credentials",
        "MYSQL Invalid port",
        "MYSQL Invalid host",
    ],
)
@pytest.mark.asyncio
async def unreachable_external_db_workspace(
    request,
    main_session: AsyncSession,
) -> AsyncGenerator[Workspace, None]:
    workspace = Workspace(
        name="Duché de Normandie",
        domain="normandie.localhost:8000",
        database_type=request.param["type"],
        database_host=request.param["host"],
        database_port=request.param["port"],
        database_username="guillaume",
        database_password="alienor",
        database_name="fief_normandy",
        alembic_revision="LATEST",
    )
    main_session.add(workspace)
    await main_session.commit()

    yield workspace

    await main_session.delete(workspace)
    await main_session.commit()


@pytest.fixture(scope="module")
@pytest.mark.asyncio
async def outdated_migration_workspace(
    main_test_database: Tuple[engine.URL, DatabaseType],
    main_session: AsyncSession,
) -> AsyncGenerator[Workspace, None]:
    url, database_type = main_test_database
    workspace = Workspace(
        name="Duché de Savoie",
        domain="savoie.localhost:8000",
        database_type=database_type,
        database_host=url.host,
        database_port=url.port,
        database_username=url.username,
        database_password=url.password,
        database_name=url.database,
        alembic_revision=None,
    )
    main_session.add(workspace)
    await main_session.commit()

    yield workspace

    await main_session.delete(workspace)
    await main_session.commit()


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
        del app.dependency_overrides[get_current_workspace_session]
        yield test_client


@pytest.mark.asyncio
class TestGetCurrentWorkspaceFromHostHeader:
    async def test_not_existing_workspace(self, test_client_auth: httpx.AsyncClient):
        response = await test_client_auth.get(
            "/workspace", headers={"Host": "unknown.fief.dev"}
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    async def test_outdated_migration_workspace(
        self,
        test_client_auth: httpx.AsyncClient,
        outdated_migration_workspace: Workspace,
    ):
        response = await test_client_auth.get(
            "/workspace", headers={"Host": outdated_migration_workspace.domain}
        )

        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

        json = response.json()
        assert json["detail"] == APIErrorCode.WORKSPACE_DB_OUTDATED_MIGRATION

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
    async def test_unreachable_external_db_workspace(
        self,
        test_client_auth: httpx.AsyncClient,
        unreachable_external_db_workspace: Workspace,
    ):
        response = await test_client_auth.get(
            "/tenants", headers={"Host": unreachable_external_db_workspace.domain}
        )

        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

        json = response.json()
        assert json["detail"] == APIErrorCode.WORKSPACE_DB_CONNECTION_ERROR

    async def test_existing_workspace(
        self, test_client_auth: httpx.AsyncClient, workspace: Workspace
    ):
        response = await test_client_auth.get(
            "/tenants", headers={"Host": workspace.domain}
        )

        assert response.status_code == status.HTTP_200_OK

        json = response.json()
        assert json["count"] == 2
