import json
import uuid
from collections.abc import AsyncGenerator

import pytest
from fastapi import Depends, FastAPI, status

from fief.crypto.token import generate_token
from fief.db import AsyncSession
from fief.dependencies.admin_authentication import (
    is_authenticated_admin_api,
    is_authenticated_admin_session,
)
from fief.models import AdminAPIKey, AdminSessionToken, Workspace, WorkspaceUser
from fief.settings import settings
from tests.types import HTTPClientGeneratorType


@pytest.fixture
def app() -> FastAPI:
    app = FastAPI()

    @app.get("/login", name="dashboard.auth:login")
    async def login():
        return "Ok"

    @app.get("/protected-api", dependencies=[Depends(is_authenticated_admin_api)])
    async def protected_api():
        return "Ok"

    @app.get(
        "/protected-session", dependencies=[Depends(is_authenticated_admin_session)]
    )
    async def protected_session():
        return "Ok"

    return app


@pytest.fixture
async def another_workspace(
    main_session: AsyncSession,
) -> AsyncGenerator[Workspace, None]:
    workspace = Workspace(name="Gascony", domain="gascony.localhost")
    main_session.add(workspace)
    await main_session.commit()

    yield workspace

    await main_session.delete(workspace)


@pytest.mark.asyncio
@pytest.mark.workspace_host
async def test_no_authentication(
    test_client_generator: HTTPClientGeneratorType, app: FastAPI
):
    async with test_client_generator(app) as test_client:
        response = await test_client.get("/protected-api")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        response = await test_client.get("/protected-session")
        assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT


@pytest.mark.asyncio
@pytest.mark.workspace_host
async def test_admin_session_for_another_workspace(
    main_session: AsyncSession,
    not_existing_uuid: uuid.UUID,
    test_client_generator: HTTPClientGeneratorType,
    another_workspace: Workspace,
    app: FastAPI,
):
    workspace_user = WorkspaceUser(
        workspace_id=another_workspace.id, user_id=not_existing_uuid
    )
    main_session.add(workspace_user)
    token, token_hash = generate_token()
    session_token = AdminSessionToken(
        token=token_hash,
        raw_tokens="{}",
        raw_userinfo=json.dumps({"sub": str(not_existing_uuid)}),
    )
    main_session.add(session_token)
    await main_session.commit()

    async with test_client_generator(app) as test_client:
        cookies = {}
        cookies[settings.fief_admin_session_cookie_name] = token
        response = await test_client.get("/protected-session", cookies=cookies)

        assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT


@pytest.mark.asyncio
@pytest.mark.workspace_host
@pytest.mark.authenticated_admin(mode="session")
async def test_valid_admin_session(
    test_client_generator: HTTPClientGeneratorType, app: FastAPI
):
    async with test_client_generator(app) as test_client:
        response = await test_client.get("/protected-session")
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
@pytest.mark.workspace_host
async def test_admin_api_key_for_another_workspace(
    main_session: AsyncSession,
    test_client_generator: HTTPClientGeneratorType,
    another_workspace: Workspace,
    app: FastAPI,
):
    token, token_hash = generate_token()
    api_key = AdminAPIKey(
        name="Default", token=token_hash, workspace_id=another_workspace.id
    )
    main_session.add(api_key)
    await main_session.commit()

    async with test_client_generator(app) as test_client:
        headers = {"Authorization": f"Bearer {token}"}
        response = await test_client.get("/protected-api", headers=headers)
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
@pytest.mark.workspace_host
@pytest.mark.authenticated_admin(mode="api_key")
async def test_valid_admin_api_key(
    test_client_generator: HTTPClientGeneratorType, app: FastAPI
):
    async with test_client_generator(app) as test_client:
        response = await test_client.get("/protected-api")
        assert response.status_code == status.HTTP_200_OK
