import httpx
import pytest
from fastapi import status
from fastapi_users.router.common import ErrorCode as FastAPIUsersErrorCode
from furl import furl

from fief.errors import ErrorCode
from fief.models import Account
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


@pytest.mark.asyncio
@pytest.mark.test_data
class TestAuthLogin:
    async def test_missing_parameters(
        self, test_client: httpx.AsyncClient, account: Account
    ):
        response = await test_client.post(
            "/auth/login", headers={"Host": account.domain}
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_bad_credentials(
        self, test_client: httpx.AsyncClient, account: Account, test_data: TestData
    ):
        tenant = test_data["tenants"]["default"]

        response = await test_client.post(
            "/auth/login",
            data={
                "response_type": "code",
                "client_id": tenant.client_id,
                "redirect_uri": "https://bretagne.duchy/callback",
                "username": "anne@bretagne.duchy",
                "password": "foo",
            },
            headers={"Host": account.domain},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        json = response.json()
        assert json["detail"] == FastAPIUsersErrorCode.LOGIN_BAD_CREDENTIALS

    async def test_valid_credentials(
        self, test_client: httpx.AsyncClient, account: Account, test_data: TestData
    ):
        tenant = test_data["tenants"]["default"]

        response = await test_client.post(
            "/auth/login",
            data={
                "response_type": "code",
                "client_id": tenant.client_id,
                "redirect_uri": "https://bretagne.duchy/callback",
                "state": "STATE",
                "username": "anne@bretagne.duchy",
                "password": "hermine",
            },
            headers={"Host": account.domain},
        )

        assert response.status_code == status.HTTP_200_OK

        json = response.json()
        redirect_uri = json["redirect_uri"]

        assert redirect_uri.startswith("https://bretagne.duchy/callback")
        parsed_location = furl(redirect_uri)
        assert "code" in parsed_location.query.params
        assert parsed_location.query.params["state"] == "STATE"

    async def test_none_state_not_in_redirect_uri(
        self, test_client: httpx.AsyncClient, account: Account, test_data: TestData
    ):
        tenant = test_data["tenants"]["default"]

        response = await test_client.post(
            "/auth/login",
            data={
                "response_type": "code",
                "client_id": tenant.client_id,
                "redirect_uri": "https://bretagne.duchy/callback",
                "username": "anne@bretagne.duchy",
                "password": "hermine",
            },
            headers={"Host": account.domain},
        )

        assert response.status_code == status.HTTP_200_OK

        json = response.json()
        redirect_uri = json["redirect_uri"]

        parsed_location = furl(redirect_uri)
        assert "state" not in parsed_location.query.params
