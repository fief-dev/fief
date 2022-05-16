import uuid

import httpx
import pytest
from fastapi import status

from fief.errors import APIErrorCode
from tests.data import TestData


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestListUsers:
    async def test_unauthorized(self, test_client_admin: httpx.AsyncClient):
        response = await test_client_admin.get("/users/")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.parametrize(
        "ordering", ["unknown_field", "email,-unknown_field", "tenant", "tenant.name"]
    )
    @pytest.mark.authenticated_admin
    async def test_unknown_ordering_field(
        self, ordering: str, test_client_admin: httpx.AsyncClient
    ):
        response = await test_client_admin.get("/users/", params={"ordering": ordering})

        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.authenticated_admin
    async def test_valid(
        self, test_client_admin: httpx.AsyncClient, test_data: TestData
    ):
        response = await test_client_admin.get("/users/")

        assert response.status_code == status.HTTP_200_OK

        json = response.json()
        assert json["count"] == len(test_data["users"])

        for result in json["results"]:
            assert "tenant" in result


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestCreateUser:
    async def test_unauthorized(self, test_client_admin: httpx.AsyncClient):
        response = await test_client_admin.post("/users/", json={})

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.authenticated_admin
    async def test_unknown_tenant(
        self, test_client_admin: httpx.AsyncClient, not_existing_uuid: uuid.UUID
    ):
        response = await test_client_admin.post(
            "/users/",
            json={
                "email": "louis@bretagne.duchy",
                "password": "hermine1",
                "fields": {},
                "tenant_id": str(not_existing_uuid),
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        json = response.json()
        assert json["detail"] == APIErrorCode.USER_CREATE_UNKNOWN_TENANT

    @pytest.mark.authenticated_admin
    async def test_existing_user(
        self, test_client_admin: httpx.AsyncClient, test_data: TestData
    ):
        tenant = test_data["tenants"]["default"]
        response = await test_client_admin.post(
            "/users/",
            json={
                "email": "anne@bretagne.duchy",
                "password": "hermine1",
                "fields": {},
                "tenant_id": str(tenant.id),
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        json = response.json()
        assert json["detail"] == APIErrorCode.USER_CREATE_ALREADY_EXISTS

    @pytest.mark.authenticated_admin
    async def test_invalid_password(
        self, test_client_admin: httpx.AsyncClient, test_data: TestData
    ):
        tenant = test_data["tenants"]["default"]
        response = await test_client_admin.post(
            "/users/",
            json={
                "email": "louis@bretagne.duchy",
                "password": "h",
                "fields": {},
                "tenant_id": str(tenant.id),
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        json = response.json()
        assert json["detail"] == APIErrorCode.USER_CREATE_INVALID_PASSWORD
        assert "reason" in json

    @pytest.mark.authenticated_admin
    async def test_invalid_field_value(
        self, test_client_admin: httpx.AsyncClient, test_data: TestData
    ):
        tenant = test_data["tenants"]["default"]
        response = await test_client_admin.post(
            "/users/",
            json={
                "email": "louis@bretagne.duchy",
                "password": "hermine1",
                "fields": {
                    "last_seen": "INVALID_VALUE",
                },
                "tenant_id": str(tenant.id),
            },
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        json = response.json()
        assert json["detail"][0]["loc"] == ["body", "fields", "last_seen"]

    @pytest.mark.authenticated_admin
    async def test_valid(
        self, test_client_admin: httpx.AsyncClient, test_data: TestData
    ):
        tenant = test_data["tenants"]["default"]
        response = await test_client_admin.post(
            "/users/",
            json={
                "email": "louis@bretagne.duchy",
                "password": "hermine1",
                "fields": {
                    "onboarding_done": True,
                    "last_seen": "2022-01-01T13:37:00+00:00",
                },
                "tenant_id": str(tenant.id),
            },
        )

        assert response.status_code == status.HTTP_201_CREATED

        json = response.json()
        assert json["email"] == "louis@bretagne.duchy"
        assert json["tenant_id"] == str(tenant.id)

        assert json["fields"]["onboarding_done"] is True
        assert json["fields"]["last_seen"] == "2022-01-01T13:37:00+00:00"
