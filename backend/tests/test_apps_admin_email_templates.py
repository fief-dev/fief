import uuid

import httpx
import pytest
from fastapi import status

from fief import schemas
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
    async def test_unauthorized(self, test_client_admin: httpx.AsyncClient):
        response = await test_client_admin.post(
            "/email-templates/preview",
            json={
                "type": schemas.email_template.EmailTemplateType.WELCOME,
                "subject": "SUBJECT",
                "content": "CONTENT",
            },
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.authenticated_admin
    @pytest.mark.parametrize(
        "type,subject_input,subject_output,content_input,content_output",
        [
            (
                "BASE",
                "",
                "",
                "<html>{{ tenant.name }}</html>",
                "<html>Default</html>",
            ),
            (
                "WELCOME",
                "Hello, {{ user.email }}",
                "Hello, anne@bretagne.duchy",
                "{% extends 'BASE' %}{% block main %}WELCOME, {{ user.email }}{% endblock %}",
                "<html><body><h1>Default</h1>WELCOME, anne@bretagne.duchy</body></html>",
            ),
            (
                "FORGOT_PASSWORD",
                "Password forgot, {{ user.email }}",
                "Password forgot, anne@bretagne.duchy",
                "{% extends 'BASE' %}{% block main %}FORGOT_PASSWORD, {{ user.email }} {{ reset_url }}{% endblock %}",
                "<html><body><h1>Default</h1>FORGOT_PASSWORD, anne@bretagne.duchy https://example.fief.dev/reset</body></html>",
            ),
        ],
    )
    async def test_valid(
        self,
        type: str,
        subject_input: str,
        subject_output: str,
        content_input: str,
        content_output: str,
        test_client_admin: httpx.AsyncClient,
    ):
        response = await test_client_admin.post(
            "/email-templates/preview",
            json={"type": type, "subject": subject_input, "content": content_input},
        )

        assert response.status_code == status.HTTP_200_OK

        json = response.json()
        assert json["subject"] == subject_output
        assert json["content"] == content_output


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
