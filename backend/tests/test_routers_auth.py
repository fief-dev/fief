import httpx
import pytest
from fastapi import status

from fief.errors import ErrorCode
from fief.models import Account
from tests.data import TestData


@pytest.mark.asyncio
@pytest.mark.test_data
class TestAuthLogin:
    async def test_not_existing_account(self, test_client: httpx.AsyncClient):
        response = await test_client.post(
            "/auth/login",
            headers={"Host": "unknown.fief.dev"},
            data={"username": "anne@bretagne.duchy", "password": "hermine"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    async def test_bad_credentials(
        self, test_client: httpx.AsyncClient, account: Account
    ):
        response = await test_client.post(
            "/auth/login",
            headers={"Host": account.domain},
            data={"username": "anne@bretagne.duchy", "password": "foo"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    async def test_success(self, test_client: httpx.AsyncClient, account: Account):
        response = await test_client.post(
            "/auth/login",
            headers={"Host": account.domain},
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
            "/auth/login",
            headers={
                "Host": account.domain,
                "x-fief-tenant": str(test_data["tenants"]["secondary"].id),
            },
            data={"username": "anne@bretagne.duchy", "password": "hermine"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.asyncio
@pytest.mark.test_data
class TestAuthAuthorize:
    async def test_missing_client_id(
        self, test_client: httpx.AsyncClient, account: Account
    ):
        response = await test_client.get(
            "/auth/authorize", headers={"Host": account.domain}
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_unknown_client_id(
        self, test_client: httpx.AsyncClient, account: Account
    ):
        response = await test_client.get(
            "/auth/authorize",
            params={"client_id": "UNKNOWN"},
            headers={"Host": account.domain},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        json = response.json()
        assert json["detail"] == ErrorCode.AUTH_INVALID_CLIENT_ID

    async def test_valid_client_id(
        self, test_client: httpx.AsyncClient, test_data: TestData, account: Account
    ):
        tenant = test_data["tenants"]["default"]

        response = await test_client.get(
            "/auth/authorize",
            params={"client_id": tenant.client_id},
            headers={"Host": account.domain},
        )

        assert response.status_code == status.HTTP_200_OK

        json = response.json()
        assert json["id"] == str(tenant.id)
        assert "client_id" not in json
        assert "client_secret" not in json
