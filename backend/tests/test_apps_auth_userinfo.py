import httpx
import pytest
from fastapi import status

from tests.data import TestData


@pytest.mark.asyncio
@pytest.mark.test_data
@pytest.mark.account_host
class TestUserUserinfo:
    @pytest.mark.parametrize(
        "path_prefix",
        [
            (""),
            ("/secondary"),
        ],
    )
    async def test_unauthorized(
        self, path_prefix: str, test_client_auth: httpx.AsyncClient
    ):
        response = await test_client_auth.get(f"{path_prefix}/userinfo")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.parametrize(
        "path_prefix,user_alias",
        [
            pytest.param("", "regular", marks=pytest.mark.access_token(user="regular")),
            pytest.param(
                "/secondary",
                "regular_secondary",
                marks=pytest.mark.access_token(user="regular_secondary"),
            ),
        ],
    )
    async def test_authorized(
        self,
        path_prefix: str,
        user_alias: str,
        test_client_auth: httpx.AsyncClient,
        test_data: TestData,
    ):
        response = await test_client_auth.get(f"{path_prefix}/userinfo")

        assert response.status_code == status.HTTP_200_OK

        user = test_data["users"][user_alias]

        json = response.json()
        assert json == {
            "sub": str(user.id),
            "email": user.email,
            "tenant_id": str(user.tenant_id),
        }
