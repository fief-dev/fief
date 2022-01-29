import httpx
import pytest
from fastapi import status
from sqlalchemy import select

from fief.db import AsyncSession
from fief.models import User
from fief.models.tenant import Tenant
from tests.data import TestData


@pytest.mark.asyncio
@pytest.mark.account_host
class TestRegister:
    async def test_existing_user(self, test_client_auth: httpx.AsyncClient):
        response = await test_client_auth.post(
            "/register", json={"email": "anne@bretagne.duchy", "password": "hermine"}
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["detail"] != "Bad Request"

    async def test_new_user(self, test_client_auth: httpx.AsyncClient):
        response = await test_client_auth.post(
            "/register", json={"email": "louis@bretagne.duchy", "password": "hermine"}
        )

        assert response.status_code == status.HTTP_201_CREATED

        json = response.json()
        assert "id" in json

    async def test_new_user2(self, test_client_auth: httpx.AsyncClient):
        response = await test_client_auth.post(
            "/register", json={"email": "louis@bretagne.duchy", "password": "hermine"}
        )

        assert response.status_code == status.HTTP_201_CREATED

        json = response.json()
        assert "id" in json

    async def test_no_email_conflict_on_another_tenant(
        self, test_client_auth: httpx.AsyncClient, test_data: TestData
    ):
        response = await test_client_auth.post(
            f"/{test_data['tenants']['secondary'].slug}/register",
            json={"email": "anne@bretagne.duchy", "password": "hermine"},
        )

        assert response.status_code == status.HTTP_201_CREATED

        json = response.json()
        assert "id" in json


@pytest.mark.asyncio
class TestFFS:
    async def test_ffs1(self, account_session: AsyncSession, test_data: TestData):
        user = User(
            email="foo@bar.com",
            hashed_password="aaa",
            tenant=test_data["tenants"]["default"],
        )
        account_session.add(user)
        await account_session.commit()

        stmt = select(User).where(User.email == "foo@bar.com")
        r = await account_session.execute(stmt)
        assert len(r.all()) == 1

    async def test_ffs2(self, account_session: AsyncSession, test_data: TestData):
        stmt = select(Tenant)
        r = await account_session.execute(stmt)
        assert len(r.all()) > 0

        user = User(
            email="foo@bar.com",
            hashed_password="aaa",
            tenant=test_data["tenants"]["default"],
        )
        account_session.add(user)
        await account_session.commit()

        stmt = select(User).where(User.email == "foo@bar.com")
        r = await account_session.execute(stmt)
        assert len(r.all()) == 1
