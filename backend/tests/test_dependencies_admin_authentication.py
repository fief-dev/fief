import json
import uuid
from typing import AsyncGenerator

import pytest
from fastapi import Depends, FastAPI, status

from fief.crypto.token import generate_token
from fief.db import AsyncSession
from fief.dependencies.admin_authentication import is_authenticated_admin
from fief.models import AdminAPIKey, AdminSessionToken, Workspace, WorkspaceUser
from fief.settings import settings
from tests.conftest import TestClientGeneratorType


@pytest.fixture
def app() -> FastAPI:
    app = FastAPI()

    @app.get("/protected", dependencies=[Depends(is_authenticated_admin)])
    async def protected():
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
    test_client_admin_generator: TestClientGeneratorType, app: FastAPI
):
    async with test_client_admin_generator(app) as test_client:
        response = await test_client.get("/protected")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
@pytest.mark.workspace_host
async def test_admin_session_for_another_workspace(
    main_session: AsyncSession,
    not_existing_uuid: uuid.UUID,
    test_client_admin_generator: TestClientGeneratorType,
    another_workspace: Workspace,
    app: FastAPI,
):
    workspace_user = WorkspaceUser(
        workspace_id=another_workspace.id, user_id=not_existing_uuid
    )
    main_session.add(workspace_user)
    session_token = AdminSessionToken(
        raw_tokens="{}", raw_userinfo=json.dumps({"sub": str(not_existing_uuid)})
    )
    main_session.add(session_token)
    await main_session.commit()

    async with test_client_admin_generator(app) as test_client:
        cookies = {}
        cookies[settings.fief_admin_session_cookie_name] = session_token.token
        response = await test_client.get("/protected", cookies=cookies)

        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
@pytest.mark.workspace_host
@pytest.mark.authenticated_admin(mode="session")
async def test_valid_admin_session(
    test_client_admin_generator: TestClientGeneratorType, app: FastAPI
):
    async with test_client_admin_generator(app) as test_client:
        response = await test_client.get("/protected")
        print(response.json())
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
@pytest.mark.workspace_host
async def test_admin_api_key_for_another_workspace(
    main_session: AsyncSession,
    test_client_admin_generator: TestClientGeneratorType,
    another_workspace: Workspace,
    app: FastAPI,
):
    token, token_hash = generate_token()
    api_key = AdminAPIKey(
        name="Default", token=token_hash, workspace_id=another_workspace.id
    )
    main_session.add(api_key)
    await main_session.commit()

    async with test_client_admin_generator(app) as test_client:
        headers = {"Authorization": f"Bearer {token}"}
        response = await test_client.get("/protected", headers=headers)

        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
@pytest.mark.workspace_host
@pytest.mark.authenticated_admin(mode="api_key")
async def test_valid_admin_api_key(
    test_client_admin_generator: TestClientGeneratorType, app: FastAPI
):
    async with test_client_admin_generator(app) as test_client:
        response = await test_client.get("/protected")
        print(response.json())
        assert response.status_code == status.HTTP_200_OK
