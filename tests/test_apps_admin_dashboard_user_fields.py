import uuid
from typing import Any

import httpx
import pytest
from bs4 import BeautifulSoup
from fastapi import status

from fief.db import AsyncSession
from fief.models import Workspace
from fief.repositories import UserFieldRepository
from tests.data import TestData
from tests.helpers import HTTPXResponseAssertion


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestListUserFields:
    async def test_unauthorized(
        self,
        unauthorized_dashboard_assertions: HTTPXResponseAssertion,
        test_client_admin_dashboard: httpx.AsyncClient,
    ):
        response = await test_client_admin_dashboard.get("/user-fields/")

        unauthorized_dashboard_assertions(response)

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="main")
    async def test_valid(
        self, test_client_admin_dashboard: httpx.AsyncClient, test_data: TestData
    ):
        response = await test_client_admin_dashboard.get("/user-fields/")

        assert response.status_code == status.HTTP_200_OK

        html = BeautifulSoup(response.text, features="html.parser")
        rows = html.find("tbody").find_all("tr")
        assert len(rows) == len(test_data["user_fields"])


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestGetUserField:
    async def test_unauthorized(
        self,
        unauthorized_dashboard_assertions: HTTPXResponseAssertion,
        test_client_admin_dashboard: httpx.AsyncClient,
        test_data: TestData,
    ):
        response = await test_client_admin_dashboard.get(
            f"/user-fields/{test_data['user_fields']['given_name'].id}"
        )

        unauthorized_dashboard_assertions(response)

    @pytest.mark.authenticated_admin(mode="session")
    async def test_not_existing(
        self,
        test_client_admin_dashboard: httpx.AsyncClient,
        not_existing_uuid: uuid.UUID,
    ):
        response = await test_client_admin_dashboard.get(
            f"/user-fields/{not_existing_uuid}"
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="aside")
    async def test_valid(
        self, test_client_admin_dashboard: httpx.AsyncClient, test_data: TestData
    ):
        user_field = test_data["user_fields"]["given_name"]
        response = await test_client_admin_dashboard.get(
            f"/user-fields/{user_field.id}"
        )

        assert response.status_code == status.HTTP_200_OK

        html = BeautifulSoup(response.text, features="html.parser")
        title = html.find("h2")
        assert user_field.name in title.text


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestCreateUserField:
    async def test_unauthorized(
        self,
        unauthorized_dashboard_assertions: HTTPXResponseAssertion,
        test_client_admin_dashboard: httpx.AsyncClient,
    ):
        response = await test_client_admin_dashboard.post(
            "/user-fields/create", data={}
        )

        unauthorized_dashboard_assertions(response)

    @pytest.mark.parametrize(
        "type,has_default",
        [
            ("STRING", True),
            ("INTEGER", True),
            ("BOOLEAN", True),
            ("DATE", False),
            ("DATETIME", False),
            ("CHOICE", True),
            ("PHONE_NUMBER", False),
            ("ADDRESS", False),
            ("TIMEZONE", True),
        ],
    )
    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_configuration_default_display(
        self,
        type: str,
        has_default: bool,
        test_client_admin_dashboard: httpx.AsyncClient,
        csrf_token: str,
    ):
        response = await test_client_admin_dashboard.post(
            "/user-fields/create",
            data={
                "type": type,
                "csrf_token": csrf_token,
            },
            headers={"HX-Trigger": "change"},
        )

        assert response.status_code == status.HTTP_200_OK

        html = BeautifulSoup(response.text, features="html.parser")
        field = html.find(id="configuration-default")
        if has_default:
            assert field is not None
        else:
            assert field is None

    @pytest.mark.parametrize(
        "choices",
        [
            [],
            [("a", "Choice A"), ("b", "Choice B"), ("c", "Choice C")],
        ],
    )
    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_configuration_choices_display(
        self,
        choices: list[tuple[str, str]],
        test_client_admin_dashboard: httpx.AsyncClient,
        csrf_token: str,
    ):
        data_choices = {}
        for i, (value, label) in enumerate(choices):
            data_choices[f"configuration-choices-{i}-value"] = value
            data_choices[f"configuration-choices-{i}-label"] = label

        response = await test_client_admin_dashboard.post(
            "/user-fields/create",
            data={
                "type": "CHOICE",
                **data_choices,
                "csrf_token": csrf_token,
            },
            headers={"HX-Trigger": "change"},
        )

        assert response.status_code == status.HTTP_200_OK

        html = BeautifulSoup(response.text, features="html.parser")
        for i in range(len(choices) or 1):
            assert html.find(id=f"configuration-choices-{i}-value") is not None
            assert html.find(id=f"configuration-choices-{i}-label") is not None

        default_field = html.find("select", id="configuration-default")
        assert len(default_field.find_all("option")) == len(choices) + 1

    @pytest.mark.parametrize("payload", [{}, {"type": "UNKNOWN_TYPE"}])
    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_invalid(
        self,
        payload: dict[str, Any],
        test_client_admin_dashboard: httpx.AsyncClient,
        csrf_token: str,
    ):
        response = await test_client_admin_dashboard.post(
            "/user-fields/create",
            data={
                **payload,
                "csrf_token": csrf_token,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.parametrize(
        "type,default",
        [
            ("INTEGER", "INVALID_VALUE"),
            ("BOOLEAN", "INVALID_VALUE"),
            ("TIMEZONE", "INVALID_VALUE"),
        ],
    )
    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_invalid_default(
        self,
        type: str,
        default: str,
        test_client_admin_dashboard: httpx.AsyncClient,
        csrf_token: str,
    ):
        response = await test_client_admin_dashboard.post(
            "/user-fields/create",
            data={
                "name": "Given name",
                "slug": "given_name",
                "type": type,
                "configuration-at_registration": False,
                "configuration-required": False,
                "configuration-at_update": True,
                "configuration-default": default,
                "csrf_token": csrf_token,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_already_existing_slug(
        self, test_client_admin_dashboard: httpx.AsyncClient, csrf_token: str
    ):
        response = await test_client_admin_dashboard.post(
            "/user-fields/create",
            data={
                "name": "Given name",
                "slug": "given_name",
                "type": "STRING",
                "configuration-at_registration": False,
                "configuration-required": False,
                "configuration-at_update": True,
                "csrf_token": csrf_token,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.headers["X-Fief-Error"] == "user_field_slug_already_exists"

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
            ("TIMEZONE", "Europe/Paris", "Europe/Paris"),
        ],
    )
    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_valid(
        self,
        type: str,
        default_input: str | None,
        default_output: Any | None,
        test_client_admin_dashboard: httpx.AsyncClient,
        csrf_token: str,
        workspace_session: AsyncSession,
    ):
        response = await test_client_admin_dashboard.post(
            "/user-fields/create",
            data={
                "name": "New field",
                "slug": "new_field",
                "type": type,
                "configuration-at_registration": False,
                "configuration-required": False,
                "configuration-at_update": True,
                **(
                    {"configuration-default": default_input}
                    if default_input is not None
                    else {}
                ),
                "csrf_token": csrf_token,
            },
        )

        assert response.status_code == status.HTTP_201_CREATED

        user_field_repository = UserFieldRepository(workspace_session)
        user_field = await user_field_repository.get_by_id(
            uuid.UUID(response.headers["X-Fief-Object-Id"])
        )
        assert user_field is not None
        assert user_field.type == type
        assert user_field.configuration["default"] == default_output


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestUpdateUserField:
    async def test_unauthorized(
        self,
        unauthorized_dashboard_assertions: HTTPXResponseAssertion,
        test_client_admin_dashboard: httpx.AsyncClient,
        test_data: TestData,
    ):
        user_field = test_data["user_fields"]["given_name"]
        response = await test_client_admin_dashboard.post(
            f"/user-fields/{user_field.id}/edit", data={}
        )

        unauthorized_dashboard_assertions(response)

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_not_existing(
        self,
        test_client_admin_dashboard: httpx.AsyncClient,
        not_existing_uuid: uuid.UUID,
    ):
        response = await test_client_admin_dashboard.post(
            f"/user-fields/{not_existing_uuid}/edit", data={}
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_configuration_choices_display(
        self, test_client_admin_dashboard: httpx.AsyncClient, test_data: TestData
    ):
        user_field = test_data["user_fields"]["gender"]
        choices = user_field.configuration["choices"]
        assert choices is not None

        response = await test_client_admin_dashboard.get(
            f"/user-fields/{user_field.id}/edit"
        )

        assert response.status_code == status.HTTP_200_OK

        html = BeautifulSoup(response.text, features="html.parser")
        for i in range(len(choices)):
            assert html.find(id=f"configuration-choices-{i}-value") is not None
            assert html.find(id=f"configuration-choices-{i}-label") is not None

        default_field = html.find("select", id="configuration-default")
        assert len(default_field.find_all("option")) == len(choices) + 1

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_invalid(
        self,
        test_client_admin_dashboard: httpx.AsyncClient,
        test_data: TestData,
        csrf_token: str,
    ):
        user_field = test_data["user_fields"]["given_name"]
        response = await test_client_admin_dashboard.post(
            f"/user-fields/{user_field.id}/edit",
            data={
                "csrf_token": csrf_token,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_already_existing_slug(
        self,
        test_client_admin_dashboard: httpx.AsyncClient,
        test_data: TestData,
        csrf_token: str,
    ):
        user_field = test_data["user_fields"]["given_name"]
        response = await test_client_admin_dashboard.post(
            f"/user-fields/{user_field.id}/edit",
            data={
                "name": "Given name",
                "slug": "gender",
                "type": "STRING",
                "configuration-at_registration": False,
                "configuration-required": False,
                "configuration-at_update": True,
                "csrf_token": csrf_token,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.headers["X-Fief-Error"] == "user_field_slug_already_exists"

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_valid(
        self,
        test_client_admin_dashboard: httpx.AsyncClient,
        test_data: TestData,
        csrf_token: str,
        workspace_session: AsyncSession,
    ):
        user_field = test_data["user_fields"]["given_name"]
        response = await test_client_admin_dashboard.post(
            f"/user-fields/{user_field.id}/edit",
            data={
                "name": "Updated name",
                "slug": user_field.slug,
                "configuration-at_registration": user_field.configuration[
                    "at_registration"
                ],
                "configuration-required": user_field.configuration["required"],
                "configuration-at_update": user_field.configuration["at_update"],
                "csrf_token": csrf_token,
            },
        )

        assert response.status_code == status.HTTP_200_OK

        user_field_repository = UserFieldRepository(workspace_session)
        updated_user_field = await user_field_repository.get_by_id(user_field.id)
        assert updated_user_field is not None
        assert updated_user_field.name == "Updated name"

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_valid_choice(
        self,
        test_client_admin_dashboard: httpx.AsyncClient,
        test_data: TestData,
        csrf_token: str,
        workspace_session: AsyncSession,
    ):
        user_field = test_data["user_fields"]["gender"]
        response = await test_client_admin_dashboard.post(
            f"/user-fields/{user_field.id}/edit",
            data={
                "name": user_field.name,
                "slug": user_field.slug,
                "configuration-at_registration": user_field.configuration[
                    "at_registration"
                ],
                "configuration-required": user_field.configuration["required"],
                "configuration-at_update": user_field.configuration["at_update"],
                "configuration-choices-0-value": "F",
                "configuration-choices-0-label": "Foo",
                "configuration-default": "",
                "csrf_token": csrf_token,
            },
        )

        assert response.status_code == status.HTTP_200_OK

        user_field_repository = UserFieldRepository(workspace_session)
        updated_user_field = await user_field_repository.get_by_id(user_field.id)
        assert updated_user_field is not None
        assert updated_user_field.configuration["choices"] is not None
        assert updated_user_field.configuration["choices"] == [["F", "Foo"]]


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestDeleteUserField:
    async def test_unauthorized(
        self,
        unauthorized_dashboard_assertions: HTTPXResponseAssertion,
        test_client_admin_dashboard: httpx.AsyncClient,
        test_data: TestData,
    ):
        user_field = test_data["user_fields"]["given_name"]
        response = await test_client_admin_dashboard.delete(
            f"/user-fields/{user_field.id}/delete"
        )

        unauthorized_dashboard_assertions(response)

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_not_existing(
        self,
        test_client_admin_dashboard: httpx.AsyncClient,
        not_existing_uuid: uuid.UUID,
    ):
        response = await test_client_admin_dashboard.delete(
            f"/user-fields/{not_existing_uuid}/delete"
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_valid_get(
        self,
        test_client_admin_dashboard: httpx.AsyncClient,
        test_data: TestData,
        workspace: Workspace,
    ):
        user_field = test_data["user_fields"]["given_name"]
        response = await test_client_admin_dashboard.get(
            f"/user-fields/{user_field.id}/delete"
        )

        assert response.status_code == status.HTTP_200_OK

        html = BeautifulSoup(response.text, features="html.parser")
        submit_button = html.find(
            "button",
            attrs={
                "hx-delete": f"http://{workspace.domain}/user-fields/{user_field.id}/delete"
            },
        )
        assert submit_button is not None

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_valid_delete(
        self,
        test_client_admin_dashboard: httpx.AsyncClient,
        test_data: TestData,
    ):
        user_field = test_data["user_fields"]["given_name"]
        response = await test_client_admin_dashboard.delete(
            f"/user-fields/{user_field.id}/delete"
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT
