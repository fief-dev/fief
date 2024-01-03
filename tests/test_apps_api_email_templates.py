import uuid

import httpx
import pytest
from fastapi import status

from fief.errors import APIErrorCode
from tests.data import TestData
from tests.helpers import HTTPXResponseAssertion


@pytest.mark.asyncio
class TestListEmailTemplates:
    async def test_unauthorized(
        self,
        unauthorized_api_assertions: HTTPXResponseAssertion,
        test_client_api: httpx.AsyncClient,
    ):
        response = await test_client_api.get("/email-templates/")

        unauthorized_api_assertions(response)

    @pytest.mark.authenticated_admin
    async def test_valid(self, test_client_api: httpx.AsyncClient, test_data: TestData):
        response = await test_client_api.get("/email-templates/")

        assert response.status_code == status.HTTP_200_OK

        json = response.json()
        assert json["count"] == len(test_data["email_templates"])


@pytest.mark.asyncio
class TestGetEmailTemplate:
    async def test_unauthorized(
        self,
        unauthorized_api_assertions: HTTPXResponseAssertion,
        test_client_api: httpx.AsyncClient,
        test_data: TestData,
    ):
        email_template = test_data["email_templates"]["base"]
        response = await test_client_api.get(f"/email-templates/{email_template.id}")

        unauthorized_api_assertions(response)

    @pytest.mark.authenticated_admin
    async def test_not_existing(
        self, test_client_api: httpx.AsyncClient, not_existing_uuid: uuid.UUID
    ):
        response = await test_client_api.get(f"/email-templates/{not_existing_uuid}")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.authenticated_admin
    async def test_valid(
        self,
        test_client_api: httpx.AsyncClient,
        test_data: TestData,
    ):
        email_template = test_data["email_templates"]["base"]
        response = await test_client_api.get(f"/email-templates/{email_template.id}")

        assert response.status_code == status.HTTP_200_OK

        json = response.json()
        assert json["id"] == str(email_template.id)


@pytest.mark.asyncio
class TestUpdateEmailTemplate:
    async def test_unauthorized(
        self,
        unauthorized_api_assertions: HTTPXResponseAssertion,
        test_client_api: httpx.AsyncClient,
        test_data: TestData,
    ):
        email_template = test_data["email_templates"]["base"]
        response = await test_client_api.patch(
            f"/email-templates/{email_template.id}", json={}
        )

        unauthorized_api_assertions(response)

    @pytest.mark.authenticated_admin
    async def test_not_existing(
        self, test_client_api: httpx.AsyncClient, not_existing_uuid: uuid.UUID
    ):
        response = await test_client_api.patch(
            f"/email-templates/{not_existing_uuid}", json={}
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.parametrize(
        "subject_input,content_input",
        [("", "{{ foo.bar }}"), ("{{ foo.bar }}", ""), ("", "{% if %}")],
    )
    @pytest.mark.authenticated_admin
    async def test_invalid_template(
        self,
        subject_input: str,
        content_input: str,
        test_client_api: httpx.AsyncClient,
        test_data: TestData,
    ):
        email_template = test_data["email_templates"]["base"]
        response = await test_client_api.patch(
            f"/email-templates/{email_template.id}",
            json={"subject": subject_input, "content": content_input},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        json = response.json()
        assert json["detail"] == APIErrorCode.EMAIL_TEMPLATE_INVALID_TEMPLATE

    @pytest.mark.authenticated_admin
    async def test_valid(
        self,
        test_client_api: httpx.AsyncClient,
        test_data: TestData,
    ):
        email_template = test_data["email_templates"]["base"]
        response = await test_client_api.patch(
            f"/email-templates/{email_template.id}",
            json={"content": "UPDATED_CONTENT"},
        )

        assert response.status_code == status.HTTP_200_OK

        json = response.json()
        assert json["content"] == "UPDATED_CONTENT"
