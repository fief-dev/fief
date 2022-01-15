import httpx
import pytest
from fastapi import status

from tests.data import TestData


@pytest.mark.asyncio
@pytest.mark.test_data
@pytest.mark.account_host
class TestUserUserinfo:
    async def test_unauthorized(self, test_client_account: httpx.AsyncClient):
        response = await test_client_account.get("/user/userinfo")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.access_token(user="regular")
    async def test_authorized(
        self, test_client_account: httpx.AsyncClient, test_data: TestData
    ):
        response = await test_client_account.get("/user/userinfo")

        assert response.status_code == status.HTTP_200_OK

        user = test_data["users"]["regular"]

        json = response.json()
        assert json == {
            "sub": str(user.id),
            "email": user.email,
            "tenant_id": str(user.tenant_id),
        }
