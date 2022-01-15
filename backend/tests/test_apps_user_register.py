import httpx
import pytest
from fastapi import status

from tests.data import TestData


@pytest.mark.asyncio
@pytest.mark.test_data
@pytest.mark.account_host
class TestRegister:
    async def test_existing_user(self, test_client_user: httpx.AsyncClient):
        response = await test_client_user.post(
            "/register", json={"email": "anne@bretagne.duchy", "password": "hermine"}
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["detail"] != "Bad Request"

    async def test_new_user(self, test_client_user: httpx.AsyncClient):
        response = await test_client_user.post(
            "/register", json={"email": "louis@bretagne.duchy", "password": "hermine"}
        )

        assert response.status_code == status.HTTP_201_CREATED

        json = response.json()
        assert "id" in json

    async def test_no_email_conflict_on_another_tenant(
        self, test_client_user: httpx.AsyncClient, test_data: TestData
    ):
        response = await test_client_user.post(
            "/register",
            headers={"x-fief-tenant": str(test_data["tenants"]["secondary"].id)},
            json={"email": "anne@bretagne.duchy", "password": "hermine"},
        )

        assert response.status_code == status.HTTP_201_CREATED

        json = response.json()
        assert "id" in json
