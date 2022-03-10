import json
import uuid

import pytest
from fastapi import Depends, FastAPI, status

from fief.db import AsyncSession
from fief.dependencies.account_user import get_current_account_user
from fief.models import Account
from fief.models.account_user import AccountUser
from fief.models.admin_session_token import AdminSessionToken
from fief.settings import settings
from tests.conftest import TestClientGeneratorType


@pytest.fixture
def app() -> FastAPI:
    app = FastAPI()

    @app.get("/protected", dependencies=[Depends(get_current_account_user)])
    async def protected():
        return "Ok"

    return app


@pytest.mark.asyncio
@pytest.mark.account_host
async def test_no_admin_session(
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
    app: FastAPI,
):
    account = Account(name="Gascony", domain="gascony.localhost")
    global_session.add(account)
    await global_session.commit()

    account_user = AccountUser(account_id=account.id, user_id=not_existing_uuid)
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
@pytest.mark.admin_session_token
async def test_valid_admin_session(
    test_client_admin_generator: TestClientGeneratorType, app: FastAPI
):
    async with test_client_admin_generator(app) as test_client:
        response = await test_client.get("/protected")

        assert response.status_code == status.HTTP_200_OK
