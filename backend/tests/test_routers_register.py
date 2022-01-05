import uuid

import httpx
import pytest
from fastapi import status

from fief.models import Account


@pytest.mark.asyncio
class TestRegister:
    async def test_missing_header(self, test_client: httpx.AsyncClient):
        response = await test_client.post(
            "/auth/register",
            headers={},
            json={"email": "anne@bretagne.duchy", "password": "hermine"},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_not_existing_account(
        self, test_client: httpx.AsyncClient, not_existing_uuid: uuid.UUID
    ):
        response = await test_client.post(
            "/auth/register",
            headers={"x-fief-account": str(not_existing_uuid)},
            json={"email": "anne@bretagne.duchy", "password": "hermine"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    async def test_existing_account(
        self, test_client: httpx.AsyncClient, account: Account
    ):
        response = await test_client.post(
            "/auth/register",
            headers={"x-fief-account": str(account.id)},
            json={"email": "anne@bretagne.duchy", "password": "hermine"},
        )

        assert response.status_code == status.HTTP_201_CREATED

        json = response.json()
        assert "id" in json
