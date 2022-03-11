import json
import uuid
from typing import AsyncGenerator

import pytest
from fastapi import Depends, FastAPI, status

from fief.db import AsyncSession
from fief.dependencies.admin_authentication import is_authenticated_admin
from fief.models import Account, AccountUser, AdminAPIKey, AdminSessionToken
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
async def another_account(
    global_session: AsyncSession,
) -> AsyncGenerator[Account, None]:
    account = Account(name="Gascony", domain="gascony.localhost")
    global_session.add(account)
    await global_session.commit()

    yield account

    await global_session.delete(account)
    # await global_session.commit()


@pytest.mark.asyncio
@pytest.mark.account_host
async def test_no_authentication(
    test_client_admin_generator: TestClientGeneratorType, app: FastAPI
):
    async with test_client_admin_generator(app) as test_client:
        response = await test_client.get("/protected")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.asyncio
@pytest.mark.account_host
async def test_admin_session_for_another_account(
    global_session: AsyncSession,
    not_existing_uuid: uuid.UUID,
    test_client_admin_generator: TestClientGeneratorType,
    another_account: Account,
    app: FastAPI,
):
    account_user = AccountUser(account_id=another_account.id, user_id=not_existing_uuid)
    global_session.add(account_user)
    session_token = AdminSessionToken(
        raw_tokens="{}", raw_userinfo=json.dumps({"sub": str(not_existing_uuid)})
    )
    global_session.add(session_token)
    await global_session.commit()

    async with test_client_admin_generator(app) as test_client:
        cookies = {}
        cookies[settings.fief_admin_session_cookie_name] = session_token.token
        response = await test_client.get("/protected", cookies=cookies)

        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
@pytest.mark.account_host
@pytest.mark.authenticated_admin(mode="session")
async def test_valid_admin_session(
    test_client_admin_generator: TestClientGeneratorType, app: FastAPI
):
    async with test_client_admin_generator(app) as test_client:
        response = await test_client.get("/protected")
        print(response.json())
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
@pytest.mark.account_host
async def test_admin_api_key_for_another_account(
    global_session: AsyncSession,
    test_client_admin_generator: TestClientGeneratorType,
    another_account: Account,
    app: FastAPI,
):
    api_key = AdminAPIKey(name="Default", account_id=another_account.id)
    global_session.add(api_key)
    await global_session.commit()

    async with test_client_admin_generator(app) as test_client:
        headers = {"Authorization": f"Bearer {api_key.token}"}
        response = await test_client.get("/protected", headers=headers)

        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.asyncio
@pytest.mark.account_host
@pytest.mark.authenticated_admin(mode="api_key")
async def test_valid_admin_api_key(
    test_client_admin_generator: TestClientGeneratorType, app: FastAPI
):
    async with test_client_admin_generator(app) as test_client:
        response = await test_client.get("/protected")
        print(response.json())
        assert response.status_code == status.HTTP_200_OK
