import uuid

import httpx
import pytest
from fastapi import status

from tests.data import TestData


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestListEmailTemplates:
    async def test_unauthorized(self, test_client_admin: httpx.AsyncClient):
        response = await test_client_admin.get("/email-templates/")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.authenticated_admin
    async def test_valid(
        self, test_client_admin: httpx.AsyncClient, test_data: TestData
    ):
        response = await test_client_admin.get("/email-templates/")

        assert response.status_code == status.HTTP_200_OK

        json = response.json()
        assert json["count"] == len(test_data["email_templates"])


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestGetEmailTemplate:
    async def test_unauthorized(
        self, test_client_admin: httpx.AsyncClient, test_data: TestData
    ):
        email_template = test_data["email_templates"]["base"]
        response = await test_client_admin.get(f"/email-templates/{email_template.id}")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.authenticated_admin
    async def test_not_existing(
        self, test_client_admin: httpx.AsyncClient, not_existing_uuid: uuid.UUID
    ):
        response = await test_client_admin.get(f"/email-templates/{not_existing_uuid}")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.authenticated_admin
    async def test_valid(
        self,
        test_client_admin: httpx.AsyncClient,
        test_data: TestData,
    ):
        email_template = test_data["email_templates"]["base"]
        response = await test_client_admin.get(f"/email-templates/{email_template.id}")

        assert response.status_code == status.HTTP_200_OK

        json = response.json()
        assert json["id"] == str(email_template.id)


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestPreviewEmailTemplate:
    async def test_unauthorized(
        self, test_client_admin: httpx.AsyncClient, test_data: TestData
    ):
        email_template = test_data["email_templates"]["base"]
        response = await test_client_admin.get(
            f"/email-templates/{email_template.id}/preview"
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.authenticated_admin
    async def test_not_existing(
        self, test_client_admin: httpx.AsyncClient, not_existing_uuid: uuid.UUID
    ):
        response = await test_client_admin.get(
            f"/email-templates/{not_existing_uuid}/preview"
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.authenticated_admin
    @pytest.mark.parametrize(
        "type,subject,content",
        [
            ("base", "", "<html><body><h1>Default</h1></body></html>"),
            ("welcome", "TITLE", "<html><body><h1>Default</h1>WELCOME</body></html>"),
            (
                "forgot_password",
                "TITLE",
                "<html><body><h1>Default</h1>FORGOT_PASSWORD https://example.fief.dev/reset</body></html>",
            ),
        ],
    )
    async def test_valid(
        self,
        type: str,
        subject: str,
        content: str,
        test_client_admin: httpx.AsyncClient,
        test_data: TestData,
    ):
        email_template = test_data["email_templates"][type]
        response = await test_client_admin.get(
            f"/email-templates/{email_template.id}/preview"
        )

        assert response.status_code == status.HTTP_200_OK

        json = response.json()
        assert json["subject"] == subject
        assert json["content"] == content


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestUpdateEmailTemplate:
    async def test_unauthorized(
        self, test_client_admin: httpx.AsyncClient, test_data: TestData
    ):
        email_template = test_data["email_templates"]["base"]
        response = await test_client_admin.patch(
            f"/email-templates/{email_template.id}", json={}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.authenticated_admin
    async def test_not_existing(
        self, test_client_admin: httpx.AsyncClient, not_existing_uuid: uuid.UUID
    ):
        response = await test_client_admin.patch(
            f"/email-templates/{not_existing_uuid}", json={}
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.authenticated_admin
    async def test_valid(
        self,
        test_client_admin: httpx.AsyncClient,
        test_data: TestData,
    ):
        email_template = test_data["email_templates"]["base"]
        response = await test_client_admin.patch(
            f"/email-templates/{email_template.id}",
            json={"content": "UPDATED_CONTENT"},
        )

        assert response.status_code == status.HTTP_200_OK

        json = response.json()
        assert json["content"] == "UPDATED_CONTENT"
