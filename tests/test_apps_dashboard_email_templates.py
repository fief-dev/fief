import uuid

import httpx
import pytest
from bs4 import BeautifulSoup
from fastapi import status

from fief.db import AsyncSession
from fief.repositories import EmailTemplateRepository
from tests.data import TestData
from tests.helpers import HTTPXResponseAssertion


@pytest.mark.asyncio
class TestListEmailTemplates:
    async def test_unauthorized(
        self,
        unauthorized_dashboard_assertions: HTTPXResponseAssertion,
        test_client_dashboard: httpx.AsyncClient,
    ):
        response = await test_client_dashboard.get("/customization/email-templates/")

        unauthorized_dashboard_assertions(response)

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="main")
    async def test_valid(
        self, test_client_dashboard: httpx.AsyncClient, test_data: TestData
    ):
        response = await test_client_dashboard.get("/customization/email-templates/")

        assert response.status_code == status.HTTP_200_OK

        html = BeautifulSoup(response.text, features="html.parser")
        rows = html.find("tbody").find_all("tr")
        assert len(rows) == len(test_data["email_templates"])


@pytest.mark.asyncio
class TestUpdateEmailTemplate:
    async def test_unauthorized(
        self,
        unauthorized_dashboard_assertions: HTTPXResponseAssertion,
        test_client_dashboard: httpx.AsyncClient,
        test_data: TestData,
    ):
        response = await test_client_dashboard.get(
            f"/customization/email-templates/{test_data['email_templates']['welcome'].id}/edit"
        )

        unauthorized_dashboard_assertions(response)

    @pytest.mark.authenticated_admin(mode="session")
    async def test_not_existing(
        self,
        test_client_dashboard: httpx.AsyncClient,
        not_existing_uuid: uuid.UUID,
    ):
        response = await test_client_dashboard.get(
            f"/customization/email-templates/{not_existing_uuid}/edit"
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="main")
    async def test_valid(
        self, test_client_dashboard: httpx.AsyncClient, test_data: TestData
    ):
        email_template = test_data["email_templates"]["welcome"]
        response = await test_client_dashboard.get(
            f"/customization/email-templates/{email_template.id}/edit"
        )

        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.parametrize(
        "alias,subject_input,subject_output,content_input,content_output",
        [
            (
                "base",
                "",
                "",
                "<html>{{ tenant.name }}</html>",
                "<html>Default</html>",
            ),
            (
                "welcome",
                "Hello, {{ user.email }}",
                "Hello, anne@bretagne.duchy",
                "{% extends 'BASE' %}{% block main %}WELCOME, {{ user.email }}{% endblock %}",
                "<html><body><h1>Default</h1>WELCOME, anne@bretagne.duchy</body></html>",
            ),
            (
                "verify_email",
                "Verify your email, {{ user.email }}",
                "Verify your email, anne@bretagne.duchy",
                "{% extends 'BASE' %}{% block main %}VERIFY_EMAIL, {{ user.email }} {{ code }}{% endblock %}",
                "<html><body><h1>Default</h1>VERIFY_EMAIL, anne@bretagne.duchy ABC123</body></html>",
            ),
            (
                "forgot_password",
                "Password forgot, {{ user.email }}",
                "Password forgot, anne@bretagne.duchy",
                "{% extends 'BASE' %}{% block main %}FORGOT_PASSWORD, {{ user.email }} {{ reset_url }}{% endblock %}",
                "<html><body><h1>Default</h1>FORGOT_PASSWORD, anne@bretagne.duchy https://example.fief.dev/reset</body></html>",
            ),
        ],
    )
    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="preview")
    async def test_valid_preview(
        self,
        alias: str,
        subject_input: str,
        subject_output: str,
        content_input: str,
        content_output: str,
        test_client_dashboard: httpx.AsyncClient,
        test_data: TestData,
        csrf_token: str,
    ):
        email_template = test_data["email_templates"][alias]
        response = await test_client_dashboard.post(
            f"/customization/email-templates/{email_template.id}/edit",
            params={"preview": True},
            data={
                "subject": subject_input,
                "content": content_input,
                "csrf_token": csrf_token,
            },
        )

        assert response.status_code == status.HTTP_200_OK

        html = BeautifulSoup(response.text, features="html.parser")
        preview = html.find("div", id="preview")
        subject_output_field = preview.find("input")
        assert subject_output_field.attrs["value"] == subject_output
        content_output_field = preview.find("iframe")
        assert content_output_field.attrs["srcdoc"] == content_output

    @pytest.mark.parametrize(
        "subject_input,content_input",
        [("", "{{ foo.bar }}"), ("{{ foo.bar }}", ""), ("", "{% if %}")],
    )
    @pytest.mark.parametrize("preview", (False, True))
    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="preview")
    async def test_invalid_template(
        self,
        subject_input: str,
        content_input: str,
        preview: bool,
        test_client_dashboard: httpx.AsyncClient,
        test_data: TestData,
        csrf_token: str,
    ):
        email_template = test_data["email_templates"]["welcome"]
        response = await test_client_dashboard.post(
            f"/customization/email-templates/{email_template.id}/edit",
            params={"preview": preview},
            data={
                "subject": subject_input,
                "content": content_input,
                "csrf_token": csrf_token,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.headers["X-Fief-Error"] == "invalid_template"

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="main")
    async def test_valid_update(
        self,
        test_client_dashboard: httpx.AsyncClient,
        test_data: TestData,
        csrf_token: str,
        main_session: AsyncSession,
    ):
        email_template = test_data["email_templates"]["welcome"]
        response = await test_client_dashboard.post(
            f"/customization/email-templates/{email_template.id}/edit",
            data={
                "subject": "UPDATED_SUBJECT",
                "content": "UPDATED_CONTENT",
                "csrf_token": csrf_token,
            },
        )

        assert response.status_code == status.HTTP_200_OK

        email_template_repository = EmailTemplateRepository(main_session)
        updated_email_template = await email_template_repository.get_by_id(
            email_template.id
        )
        assert updated_email_template is not None
        assert updated_email_template.subject == "UPDATED_SUBJECT"
        assert updated_email_template.content == "UPDATED_CONTENT"
