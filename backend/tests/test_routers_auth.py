import httpx
import pytest
from fastapi import status

from fief.errors import ErrorCode
from fief.models import Account, tenant
from tests.data import TestData


@pytest.mark.asyncio
@pytest.mark.test_data
class TestAuthAuthorize:
    async def test_missing_parameters(
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
            params={
                "response_type": "code",
                "client_id": "UNKNOWN",
                "redirect_uri": "https://bretagne.duchy/callback",
            },
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
            params={
                "response_type": "code",
                "client_id": tenant.client_id,
                "redirect_uri": "https://bretagne.duchy/callback",
            },
            headers={"Host": account.domain},
        )

        assert response.status_code == status.HTTP_200_OK

        json = response.json()
        assert json["parameters"] == {
            "response_type": "code",
            "client_id": tenant.client_id,
            "redirect_uri": "https://bretagne.duchy/callback",
            "scope": None,
            "state": None,
        }
        assert json["tenant"]["id"] == str(tenant.id)
        assert "client_secret" not in json["tenant"]
