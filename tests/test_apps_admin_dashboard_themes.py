import uuid
from unittest.mock import MagicMock

import httpx
import pytest
from bs4 import BeautifulSoup
from fastapi import status

from fief.db import AsyncSession
from fief.repositories import ThemeRepository
from tests.data import TestData
from tests.helpers import HTTPXResponseAssertion


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestListThemes:
    async def test_unauthorized(
        self,
        unauthorized_dashboard_assertions: HTTPXResponseAssertion,
        test_client_admin_dashboard: httpx.AsyncClient,
    ):
        response = await test_client_admin_dashboard.get("/customization/themes/")

        unauthorized_dashboard_assertions(response)

    @pytest.mark.authenticated_admin(mode="session")
    async def test_combobox(
        self, test_client_admin_dashboard: httpx.AsyncClient, test_data: TestData
    ):
        response = await test_client_admin_dashboard.get(
            "/customization/themes/",
            headers={"HX-Request": "true", "HX-Combobox": "true"},
        )

        assert response.status_code == status.HTTP_200_OK

        html = BeautifulSoup(response.text, features="html.parser")
        items = html.find_all("li")
        assert len(items) == len(test_data["themes"])

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="main")
    async def test_valid(
        self, test_client_admin_dashboard: httpx.AsyncClient, test_data: TestData
    ):
        response = await test_client_admin_dashboard.get("/customization/themes/")

        assert response.status_code == status.HTTP_200_OK

        html = BeautifulSoup(response.text, features="html.parser")
        rows = html.find("tbody").find_all("tr")
        assert len(rows) == len(test_data["themes"])


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestCreateTheme:
    async def test_unauthorized(
        self,
        unauthorized_dashboard_assertions: HTTPXResponseAssertion,
        test_client_admin_dashboard: httpx.AsyncClient,
    ):
        response = await test_client_admin_dashboard.post(
            "/customization/themes/create", data={}
        )

        unauthorized_dashboard_assertions(response)

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_invalid(
        self, test_client_admin_dashboard: httpx.AsyncClient, csrf_token: str
    ):
        response = await test_client_admin_dashboard.post(
            "/customization/themes/create",
            data={"csrf_token": csrf_token},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_valid(
        self,
        test_client_admin_dashboard: httpx.AsyncClient,
        csrf_token: str,
        workspace_session: AsyncSession,
    ):
        response = await test_client_admin_dashboard.post(
            "/customization/themes/create",
            data={
                "name": "New theme",
                "csrf_token": csrf_token,
            },
        )

        assert response.status_code == status.HTTP_201_CREATED

        theme_repository = ThemeRepository(workspace_session)
        theme = await theme_repository.get_by_id(
            uuid.UUID(response.headers["X-Fief-Object-Id"])
        )
        assert theme is not None
        assert theme.name == "New theme"


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestUpdateTheme:
    async def test_unauthorized(
        self,
        unauthorized_dashboard_assertions: HTTPXResponseAssertion,
        test_client_admin_dashboard: httpx.AsyncClient,
        test_data: TestData,
    ):
        response = await test_client_admin_dashboard.get(
            f"/customization/themes/{test_data['themes']['default'].id}/edit"
        )

        unauthorized_dashboard_assertions(response)

    @pytest.mark.authenticated_admin(mode="session")
    async def test_not_existing(
        self,
        test_client_admin_dashboard: httpx.AsyncClient,
        not_existing_uuid: uuid.UUID,
    ):
        response = await test_client_admin_dashboard.get(
            f"/customization/themes/{not_existing_uuid}/edit"
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="main")
    async def test_valid(
        self,
        test_client_admin_dashboard: httpx.AsyncClient,
        test_data: TestData,
        theme_preview_mock: MagicMock,
    ):
        theme = test_data["themes"]["default"]
        response = await test_client_admin_dashboard.get(
            f"/customization/themes/{theme.id}/edit"
        )

        assert response.status_code == status.HTTP_200_OK

        theme_preview_mock.preview.assert_called_once()
        theme_preview_mock.preview.call_args[0][0] == "login"

    @pytest.mark.parametrize(
        "page",
        [
            ("login",),
            ("register",),
            ("forgot_password",),
            ("reset_password",),
        ],
    )
    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="preview")
    async def test_valid_preview(
        self,
        page: str,
        test_client_admin_dashboard: httpx.AsyncClient,
        test_data: TestData,
        csrf_token: str,
        theme_preview_mock: MagicMock,
    ):
        theme = test_data["themes"]["default"]
        response = await test_client_admin_dashboard.post(
            f"/customization/themes/{theme.id}/edit",
            params={"preview": page},
            data={
                **theme.__dict__,
                "csrf_token": csrf_token,
            },
        )

        assert response.status_code == status.HTTP_200_OK

        html = BeautifulSoup(response.text, features="html.parser")
        preview = html.find("div", id="preview")
        iframe = preview.find("iframe")
        assert iframe.attrs["srcdoc"] is not None

        theme_preview_mock.preview.assert_called_once()
        theme_preview_mock.preview.call_args[0][0] == page

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="main")
    async def test_valid_update(
        self,
        test_client_admin_dashboard: httpx.AsyncClient,
        test_data: TestData,
        csrf_token: str,
        workspace_session: AsyncSession,
    ):
        theme = test_data["themes"]["default"]
        response = await test_client_admin_dashboard.post(
            f"/customization/themes/{theme.id}/edit",
            data={
                **theme.__dict__,
                "primary_color": "#ff0000",
                "csrf_token": csrf_token,
            },
        )

        assert response.status_code == status.HTTP_200_OK

        theme_repository = ThemeRepository(workspace_session)
        updated_theme = await theme_repository.get_by_id(theme.id)
        assert updated_theme is not None
        assert updated_theme.primary_color == "#ff0000"


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestSetDefaultTheme:
    async def test_unauthorized(
        self,
        unauthorized_dashboard_assertions: HTTPXResponseAssertion,
        test_client_admin_dashboard: httpx.AsyncClient,
        test_data: TestData,
    ):
        response = await test_client_admin_dashboard.post(
            f"/customization/themes/{test_data['themes']['default'].id}/default"
        )

        unauthorized_dashboard_assertions(response)

    @pytest.mark.authenticated_admin(mode="session")
    async def test_not_existing(
        self,
        test_client_admin_dashboard: httpx.AsyncClient,
        not_existing_uuid: uuid.UUID,
    ):
        response = await test_client_admin_dashboard.post(
            f"/customization/themes/{not_existing_uuid}/default"
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="main")
    async def test_valid(
        self,
        test_client_admin_dashboard: httpx.AsyncClient,
        test_data: TestData,
        workspace_session: AsyncSession,
    ):
        custom_theme = test_data["themes"]["custom"]
        response = await test_client_admin_dashboard.post(
            f"/customization/themes/{custom_theme.id}/default"
        )

        assert response.status_code == status.HTTP_200_OK

        theme_repository = ThemeRepository(workspace_session)
        for theme in await theme_repository.all():
            if theme.id == custom_theme.id:
                assert theme.default is True
            else:
                assert theme.default is False
