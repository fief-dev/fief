import uuid

import httpx
import pytest
from fastapi import status

from fief.models import Account
from tests.data import TestData


@pytest.mark.asyncio
@pytest.mark.test_data
class TestAuthLogin:
    async def test_missing_header(self, test_client: httpx.AsyncClient):
        response = await test_client.post(
            "/auth/token/login",
            data={"username": "anne@bretagne.duchy", "password": "hermine"},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_not_existing_account(
        self, test_client: httpx.AsyncClient, not_existing_uuid: uuid.UUID
    ):
        response = await test_client.post(
            "/auth/token/login",
            headers={"x-fief-account": str(not_existing_uuid)},
            data={"username": "anne@bretagne.duchy", "password": "hermine"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    async def test_bad_credentials(
        self, test_client: httpx.AsyncClient, account: Account
    ):
        response = await test_client.post(
            "/auth/token/login",
            headers={"x-fief-account": str(account.id)},
            data={"username": "anne@bretagne.duchy", "password": "foo"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    async def test_success(self, test_client: httpx.AsyncClient, account: Account):
        response = await test_client.post(
            "/auth/token/login",
            headers={"x-fief-account": str(account.id)},
            data={"username": "anne@bretagne.duchy", "password": "hermine"},
        )

        assert response.status_code == status.HTTP_200_OK

        json = response.json()
        assert "access_token" in json
        assert json["token_type"] == "bearer"

    async def test_bad_credentials_on_another_tenant(
        self, test_client: httpx.AsyncClient, account: Account, test_data: TestData
    ):
        response = await test_client.post(
            "/auth/token/login",
            headers={
                "x-fief-account": str(account.id),
                "x-fief-tenant": str(test_data["tenants"]["secondary"].id),
            },
            data={"username": "anne@bretagne.duchy", "password": "hermine"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
