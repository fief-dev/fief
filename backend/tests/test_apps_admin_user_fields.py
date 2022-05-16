import uuid
from typing import Any, Optional

import httpx
import pytest
from fastapi import status

from fief.errors import APIErrorCode
from tests.data import TestData


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestListUserFields:
    async def test_unauthorized(self, test_client_admin: httpx.AsyncClient):
        response = await test_client_admin.get("/user-fields/")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.authenticated_admin
    async def test_valid(
        self, test_client_admin: httpx.AsyncClient, test_data: TestData
    ):
        response = await test_client_admin.get("/user-fields/")

        assert response.status_code == status.HTTP_200_OK

        json = response.json()
        assert json["count"] == len(test_data["user_fields"])


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestCreateUserField:
    async def test_unauthorized(self, test_client_admin: httpx.AsyncClient):
        response = await test_client_admin.post("/user-fields/", json={})

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.authenticated_admin
    async def test_invalid_configuration(self, test_client_admin: httpx.AsyncClient):
        response = await test_client_admin.post(
            "/user-fields/",
            json={
                "name": "New field",
                "slug": "new_field",
                "type": "STRING",
                "configuration": {},
            },
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        json = response.json()
        assert json["detail"][0]["loc"][:2] == ["body", "configuration"]

    @pytest.mark.parametrize(
        "type,default",
        [
            ("INTEGER", "INVALID_VALUE"),
            ("BOOLEAN", "INVALID_VALUE"),
            ("TIMEZONE", "INVALID_VALUE"),
        ],
    )
    @pytest.mark.authenticated_admin
    async def test_invalid_default(
        self,
        type: str,
        default: str,
        test_client_admin: httpx.AsyncClient,
    ):
        response = await test_client_admin.post(
            "/user-fields/",
            json={
                "name": "Given name",
                "slug": "given_name",
                "type": type,
                "configuration": {
                    "multiple": False,
                    "at_registration": False,
                    "required": False,
                    "editable": True,
                    "default": default,
                },
            },
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        json = response.json()
        assert json["detail"][0]["loc"] == ["body", "configuration", "default"]

    @pytest.mark.authenticated_admin
    async def test_already_existing_slug(
        self, test_client_admin: httpx.AsyncClient, test_data: TestData
    ):
        response = await test_client_admin.post(
            "/user-fields/",
            json={
                "name": "Given name",
                "slug": "given_name",
                "type": "STRING",
                "configuration": {
                    "multiple": False,
                    "at_registration": False,
                    "required": False,
                    "editable": True,
                },
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        json = response.json()
        assert json["detail"] == APIErrorCode.USER_FIELD_SLUG_ALREADY_EXISTS

    @pytest.mark.parametrize(
        "type,default_input,default_output",
        [
            ("STRING", None, None),
            ("STRING", "off", "off"),
            ("STRING", "on", "on"),
            ("INTEGER", 123, 123),
            ("INTEGER", 0, 0),
            ("INTEGER", 1, 1),
            ("BOOLEAN", True, True),
            ("BOOLEAN", False, False),
            ("DATE", "2022-01-01", None),
            ("DATETIME", "2022-01-01T13:37:00+00:00", None),
            ("PHONE_NUMBER", "+33102030405", None),
            ("ADDRESS", "", None),
            ("TIMEZONE", "Europe/Paris", "Europe/Paris"),
        ],
    )
    @pytest.mark.authenticated_admin
    async def test_valid(
        self,
        type: str,
        default_input: Optional[str],
        default_output: Optional[Any],
        test_client_admin: httpx.AsyncClient,
        test_data: TestData,
    ):
        response = await test_client_admin.post(
            "/user-fields/",
            json={
                "name": "New field",
                "slug": "new_field",
                "type": type,
                "configuration": {
                    "multiple": False,
                    "at_registration": False,
                    "required": False,
                    "editable": True,
                    **({"default": default_input} if default_input is not None else {}),
                },
            },
        )

        assert response.status_code == status.HTTP_201_CREATED

        json = response.json()
        assert json["name"] == "New field"
        assert json["configuration"]["default"] == default_output


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestUpdateUserField:
    async def test_unauthorized(
        self, test_client_admin: httpx.AsyncClient, test_data: TestData
    ):
        user_field = test_data["user_fields"]["given_name"]
        response = await test_client_admin.patch(
            f"/user-fields/{user_field.id}", json={}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.authenticated_admin
    async def test_not_existing(
        self, test_client_admin: httpx.AsyncClient, not_existing_uuid: uuid.UUID
    ):
        response = await test_client_admin.patch(
            f"/user-fields/{not_existing_uuid}", json={}
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.parametrize(
        "user_field_alias,default",
        [
            ("phone_number_verified", "INVALID_VALUE"),
        ],
    )
    @pytest.mark.authenticated_admin
    async def test_invalid_default(
        self,
        user_field_alias: str,
        default: str,
        test_client_admin: httpx.AsyncClient,
        test_data: TestData,
    ):
        user_field = test_data["user_fields"][user_field_alias]
        response = await test_client_admin.patch(
            f"/user-fields/{user_field.id}",
            json={"configuration": {**user_field.configuration, "default": default}},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        json = response.json()
        assert json["detail"][0]["loc"] == ["body", "configuration", "default"]

    @pytest.mark.authenticated_admin
    async def test_already_existing_slug(
        self, test_client_admin: httpx.AsyncClient, test_data: TestData
    ):
        user_field = test_data["user_fields"]["given_name"]
        response = await test_client_admin.patch(
            f"/user-fields/{user_field.id}",
            json={"slug": "gender"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        json = response.json()
        assert json["detail"] == APIErrorCode.USER_FIELD_SLUG_ALREADY_EXISTS

    @pytest.mark.authenticated_admin
    async def test_valid(
        self, test_client_admin: httpx.AsyncClient, test_data: TestData
    ):
        user_field = test_data["user_fields"]["given_name"]
        response = await test_client_admin.patch(
            f"/user-fields/{user_field.id}",
            json={"name": "Updated name", "slug": "given_name"},
        )

        assert response.status_code == status.HTTP_200_OK

        json = response.json()
        assert json["name"] == "Updated name"


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestDeleteUserField:
    async def test_unauthorized(
        self, test_client_admin: httpx.AsyncClient, test_data: TestData
    ):
        user_field = test_data["user_fields"]["given_name"]
        response = await test_client_admin.delete(f"/user-fields/{user_field.id}")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.authenticated_admin
    async def test_not_existing(
        self, test_client_admin: httpx.AsyncClient, not_existing_uuid: uuid.UUID
    ):
        response = await test_client_admin.delete(f"/user-fields/{not_existing_uuid}")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.authenticated_admin
    async def test_valid(
        self, test_client_admin: httpx.AsyncClient, test_data: TestData
    ):
        user_field = test_data["user_fields"]["given_name"]
        response = await test_client_admin.delete(f"/user-fields/{user_field.id}")

        assert response.status_code == status.HTTP_204_NO_CONTENT
