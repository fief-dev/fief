import httpx
import pytest
from fastapi import status

from tests.data import TestData


@pytest.mark.asyncio
class TestListTenants:
    async def test_unauthorized(self, test_client_admin: httpx.AsyncClient):
        response = await test_client_admin.get("/tenants/")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.admin_session_token()
    async def test_valid(
        self, test_client_admin: httpx.AsyncClient, test_data: TestData
    ):
        response = await test_client_admin.get("/tenants/")

        assert response.status_code == status.HTTP_200_OK

        json = response.json()
        assert json["count"] == len(test_data["tenants"])

    @pytest.mark.admin_session_token()
    @pytest.mark.parametrize(
        "query,nb_results",
        [("default", 1), ("de", 1), ("SECONDARY", 1), ("unknown", 0)],
    )
    async def test_query_filter(
        self,
        query: str,
        nb_results: int,
        test_client_admin: httpx.AsyncClient,
        test_data: TestData,
    ):
        response = await test_client_admin.get("/tenants/", params={"query": query})

        assert response.status_code == status.HTTP_200_OK

        json = response.json()
        assert json["count"] == nb_results
