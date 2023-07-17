from collections.abc import AsyncGenerator

import httpx
import pytest
import pytest_asyncio
from fastapi import Depends, FastAPI, status
from sqlalchemy import select

from fief.db import AsyncSession
from fief.db.types import DatabaseConnectionParameters, DatabaseType
from fief.dependencies.current_workspace import (
    get_current_workspace,
    get_current_workspace_session,
)
from fief.errors import APIErrorCode
from fief.models import Tenant, Workspace
from tests.types import HTTPClientGeneratorType


@pytest_asyncio.fixture(
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
async def unreachable_external_db_workspace(
    request,
    latest_revision: str,
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
        alembic_revision=latest_revision,
    )
    main_session.add(workspace)
    await main_session.commit()

    yield workspace

    await main_session.delete(workspace)
    await main_session.commit()


@pytest_asyncio.fixture(scope="module")
async def outdated_migration_workspace(
    main_test_database: tuple[DatabaseConnectionParameters, DatabaseType],
    main_session: AsyncSession,
) -> AsyncGenerator[Workspace, None]:
    (url, _), database_type = main_test_database
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


@pytest_asyncio.fixture
async def test_client(
    test_client_generator: HTTPClientGeneratorType, app: FastAPI
) -> AsyncGenerator[httpx.AsyncClient, None]:
    async with test_client_generator(app) as test_client:
        app.dependency_overrides.pop(get_current_workspace_session)
        yield test_client


@pytest.mark.asyncio
class TestGetCurrentWorkspaceFromHostHeader:
    async def test_not_existing_workspace(self, test_client: httpx.AsyncClient):
        response = await test_client.get(
            "/workspace", headers={"Host": "unknown.fief.dev"}
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    async def test_outdated_migration_workspace(
        self,
        test_client: httpx.AsyncClient,
        outdated_migration_workspace: Workspace,
    ):
        response = await test_client.get(
            "/workspace", headers={"Host": outdated_migration_workspace.domain}
        )

        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

        json = response.json()
        assert json["detail"] == APIErrorCode.WORKSPACE_DB_OUTDATED_MIGRATION

    async def test_existing_workspace(
        self, test_client: httpx.AsyncClient, workspace: Workspace
    ):
        response = await test_client.get(
            "/workspace", headers={"Host": workspace.domain}
        )

        assert response.status_code == status.HTTP_200_OK

        json = response.json()
        assert json["id"] == str(workspace.id)


@pytest.mark.asyncio
class TestGetCurrentWorkspaceSession:
    async def test_unreachable_external_db_workspace(
        self,
        test_client: httpx.AsyncClient,
        unreachable_external_db_workspace: Workspace,
    ):
        response = await test_client.get(
            "/tenants", headers={"Host": unreachable_external_db_workspace.domain}
        )

        assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE

        json = response.json()
        assert json["detail"] == APIErrorCode.WORKSPACE_DB_CONNECTION_ERROR

    async def test_existing_workspace(
        self, test_client: httpx.AsyncClient, workspace: Workspace
    ):
        response = await test_client.get("/tenants", headers={"Host": workspace.domain})

        assert response.status_code == status.HTTP_200_OK

        json = response.json()
        assert json["count"] == 3
