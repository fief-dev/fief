import httpx
import pytest
from fastapi import status

from tests.data import TestData


@pytest.mark.asyncio
class TestListUsers:
    async def test_unauthorized(self, test_client_admin: httpx.AsyncClient):
        response = await test_client_admin.get("/users/")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.admin_session_token()
    async def test_valid(
        self, test_client_admin: httpx.AsyncClient, test_data: TestData
    ):
        response = await test_client_admin.get("/users/")

        assert response.status_code == status.HTTP_200_OK

        json = response.json()
        assert json["count"] == len(test_data["users"])

        for result in json["results"]:
            assert "tenant" in result
