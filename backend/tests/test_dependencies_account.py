from typing import AsyncGenerator

import httpx
import pytest
from fastapi import Depends, FastAPI, status
from sqlalchemy import select

from fief.db import AsyncSession
from fief.dependencies.account import get_current_account, get_current_account_session
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
async def test_client_dependencies(
    test_client_generator: TestClientGeneratorType, app: FastAPI
) -> AsyncGenerator[httpx.AsyncClient, None]:
    async with test_client_generator(app) as test_client:
        yield test_client


@pytest.mark.asyncio
@pytest.mark.test_data
class TestGetCurrentAccount:
    async def test_not_existing_account(
        self, test_client_dependencies: httpx.AsyncClient
    ):
        response = await test_client_dependencies.get(
            "/account", headers={"Host": "unknown.fief.dev"}
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    async def test_existing_account(
        self, test_client_dependencies: httpx.AsyncClient, account: Account
    ):
        response = await test_client_dependencies.get(
            "/account", headers={"Host": account.domain}
        )

        assert response.status_code == status.HTTP_200_OK

        json = response.json()
        assert json["id"] == str(account.id)


@pytest.mark.asyncio
@pytest.mark.test_data
class TestGetCurrentAccountSession:
    async def test_existing_account(
        self, test_client_dependencies: httpx.AsyncClient, account: Account
    ):
        response = await test_client_dependencies.get(
            "/tenants", headers={"Host": account.domain}
        )

        assert response.status_code == status.HTTP_200_OK

        json = response.json()
        assert json["count"] == 2
