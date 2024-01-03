import uuid
from typing import Any

import httpx
import pytest
from fastapi import status

from fief.errors import APIErrorCode
from tests.data import TestData, data_mapping
from tests.helpers import HTTPXResponseAssertion


@pytest.mark.asyncio
class TestListPermissions:
    async def test_unauthorized(
        self,
        unauthorized_api_assertions: HTTPXResponseAssertion,
        test_client_api: httpx.AsyncClient,
    ):
        response = await test_client_api.get("/permissions/")

        unauthorized_api_assertions(response)

    @pytest.mark.parametrize(
        "params,nb_results",
        [
            ({}, len(data_mapping["permissions"])),
            ({"query": "create"}, 1),
        ],
    )
    @pytest.mark.authenticated_admin
    async def test_valid(
        self,
        params: dict[str, Any],
        nb_results: int,
        test_client_api: httpx.AsyncClient,
        test_data: TestData,
    ):
        response = await test_client_api.get("/permissions/", params=params)

        assert response.status_code == status.HTTP_200_OK

        json = response.json()
        assert json["count"] == nb_results


@pytest.mark.asyncio
class TestGetPermission:
    async def test_unauthorized(
        self,
        unauthorized_api_assertions: HTTPXResponseAssertion,
        test_client_api: httpx.AsyncClient,
        test_data: TestData,
    ):
        permission = test_data["permissions"]["castles:create"]
        response = await test_client_api.get(f"/permissions/{permission.id}")

        unauthorized_api_assertions(response)

    @pytest.mark.authenticated_admin
    async def test_not_existing(
        self, test_client_api: httpx.AsyncClient, not_existing_uuid: uuid.UUID
    ):
        response = await test_client_api.get(f"/permissions/{not_existing_uuid}")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.authenticated_admin
    async def test_valid(self, test_client_api: httpx.AsyncClient, test_data: TestData):
        permission = test_data["permissions"]["castles:create"]
        response = await test_client_api.get(f"/permissions/{permission.id}")

        assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
class TestCreatePermission:
    async def test_unauthorized(
        self,
        unauthorized_api_assertions: HTTPXResponseAssertion,
        test_client_api: httpx.AsyncClient,
    ):
        response = await test_client_api.post("/permissions/", json={})

        unauthorized_api_assertions(response)

    @pytest.mark.authenticated_admin
    async def test_already_existing_codename(
        self, test_client_api: httpx.AsyncClient, test_data: TestData
    ):
        response = await test_client_api.post(
            "/permissions/",
            json={
                "name": "New permission",
                "codename": "castles:create",
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        json = response.json()
        assert json["detail"] == APIErrorCode.PERMISSION_CREATE_CODENAME_ALREADY_EXISTS

    @pytest.mark.authenticated_admin
    async def test_valid(self, test_client_api: httpx.AsyncClient):
        response = await test_client_api.post(
            "/permissions/",
            json={
                "name": "New permission",
                "codename": "new_permission",
            },
        )

        assert response.status_code == status.HTTP_201_CREATED

        json = response.json()
        assert json["name"] == "New permission"
        assert json["codename"] == "new_permission"


@pytest.mark.asyncio
class TestUpdatePermission:
    async def test_unauthorized(
        self,
        unauthorized_api_assertions: HTTPXResponseAssertion,
        test_client_api: httpx.AsyncClient,
        test_data: TestData,
    ):
        permission = test_data["permissions"]["castles:create"]
        response = await test_client_api.patch(f"/permissions/{permission.id}", json={})

        unauthorized_api_assertions(response)

    @pytest.mark.authenticated_admin
    async def test_not_existing(
        self, test_client_api: httpx.AsyncClient, not_existing_uuid: uuid.UUID
    ):
        response = await test_client_api.patch(
            f"/permissions/{not_existing_uuid}", json={}
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.authenticated_admin
    async def test_already_existing_codename(
        self, test_client_api: httpx.AsyncClient, test_data: TestData
    ):
        permission = test_data["permissions"]["castles:create"]
        response = await test_client_api.patch(
            f"/permissions/{permission.id}", json={"codename": "castles:update"}
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        json = response.json()
        assert json["detail"] == APIErrorCode.PERMISSION_UPDATE_CODENAME_ALREADY_EXISTS

    @pytest.mark.parametrize(
        "payload",
        [
            {"name": "Updated name"},
            {"codename": "castles:create"},
        ],
    )
    @pytest.mark.authenticated_admin
    async def test_valid(
        self,
        payload: dict[str, str],
        test_client_api: httpx.AsyncClient,
        test_data: TestData,
    ):
        permission = test_data["permissions"]["castles:create"]
        response = await test_client_api.patch(
            f"/permissions/{permission.id}", json=payload
        )

        assert response.status_code == status.HTTP_200_OK

        json = response.json()
        for field, value in payload.items():
            assert json[field] == value


@pytest.mark.asyncio
class TestDeletePermission:
    async def test_unauthorized(
        self,
        unauthorized_api_assertions: HTTPXResponseAssertion,
        test_client_api: httpx.AsyncClient,
        test_data: TestData,
    ):
        permission = test_data["permissions"]["castles:create"]
        response = await test_client_api.delete(f"/permissions/{permission.id}")

        unauthorized_api_assertions(response)

    @pytest.mark.authenticated_admin
    async def test_not_existing(
        self, test_client_api: httpx.AsyncClient, not_existing_uuid: uuid.UUID
    ):
        response = await test_client_api.delete(f"/permissions/{not_existing_uuid}")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.authenticated_admin
    async def test_valid(self, test_client_api: httpx.AsyncClient, test_data: TestData):
        permission = test_data["permissions"]["castles:create"]
        response = await test_client_api.delete(f"/permissions/{permission.id}")

        assert response.status_code == status.HTTP_204_NO_CONTENT
