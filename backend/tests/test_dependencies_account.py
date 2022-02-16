from typing import AsyncGenerator, Dict

import httpx
import pytest
from fastapi import Depends, FastAPI, status
from sqlalchemy import select

from fief.db import AsyncSession
from fief.dependencies.current_account import (
    get_current_account,
    get_current_account_session,
)
from fief.models import Account, Tenant
from tests.conftest import TestClientGeneratorType


@pytest.fixture
def app() -> FastAPI:
    app = FastAPI()

    @app.get("/account")
    async def current_account(account: Account = Depends(get_current_account)):
        return {"id": str(account.id)}

    @app.get("/tenants")
    async def current_account_tenants(
        session: AsyncSession = Depends(get_current_account_session),
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
class TestGetCurrentAccountFromHostHeader:
    async def test_not_existing_account(self, test_client_auth: httpx.AsyncClient):
        response = await test_client_auth.get(
            "/account", headers={"Host": "unknown.fief.dev"}
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    async def test_existing_account(
        self, test_client_auth: httpx.AsyncClient, account: Account
    ):
        response = await test_client_auth.get(
            "/account", headers={"Host": account.domain}
        )

        assert response.status_code == status.HTTP_200_OK

        json = response.json()
        assert json["id"] == str(account.id)


@pytest.mark.asyncio
class TestGetCurrentAccountFromAdminSession:
    async def test_unauthorized(
        self, test_client_admin_generator: TestClientGeneratorType, app: FastAPI
    ):
        async with test_client_admin_generator(app) as test_client_admin:
            response = await test_client_admin.get("/account")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.admin_session_token()
    @pytest.mark.parametrize(
        "cookies,status_code",
        [
            ({}, status.HTTP_400_BAD_REQUEST),
            (
                {"fief_account_id": "INVALID_ACCOUNT_ID"},
                status.HTTP_422_UNPROCESSABLE_ENTITY,
            ),
            (
                {"fief_account_id": "fc273aa3-17c1-4444-bc2c-b93d03afafa3"},
                status.HTTP_400_BAD_REQUEST,
            ),
        ],
    )
    async def test_valid_session_invalid_account_cookie(
        self,
        cookies: Dict[str, str],
        status_code: str,
        test_client_admin_generator: TestClientGeneratorType,
        app: FastAPI,
    ):
        async with test_client_admin_generator(app) as test_client_admin:
            response = await test_client_admin.get("/account", cookies=cookies)

        assert response.status_code == status_code

    @pytest.mark.admin_session_token()
    async def test_valid(
        self,
        test_client_admin_generator: TestClientGeneratorType,
        app: FastAPI,
        account: Account,
    ):
        async with test_client_admin_generator(app) as test_client_admin:
            response = await test_client_admin.get(
                "/account", cookies={"fief_account_id": str(account.id)}
            )

        assert response.status_code == status.HTTP_200_OK

        json = response.json()
        assert json["id"] == str(account.id)


@pytest.mark.asyncio
class TestGetCurrentAccountSession:
    async def test_existing_account(
        self, test_client_auth: httpx.AsyncClient, account: Account
    ):
        response = await test_client_auth.get(
            "/tenants", headers={"Host": account.domain}
        )

        assert response.status_code == status.HTTP_200_OK

        json = response.json()
        assert json["count"] == 2
