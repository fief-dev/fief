import uuid

import httpx
import pytest
from bs4 import BeautifulSoup
from fastapi import status

from fief.db import AsyncSession
from fief.repositories import WebhookRepository
from tests.data import TestData
from tests.helpers import HTTPXResponseAssertion


@pytest.mark.asyncio
class TestListWebhooks:
    async def test_unauthorized(
        self,
        unauthorized_dashboard_assertions: HTTPXResponseAssertion,
        test_client_dashboard: httpx.AsyncClient,
    ):
        response = await test_client_dashboard.get("/webhooks/")

        unauthorized_dashboard_assertions(response)

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="main")
    async def test_valid(
        self, test_client_dashboard: httpx.AsyncClient, test_data: TestData
    ):
        response = await test_client_dashboard.get("/webhooks/")

        assert response.status_code == status.HTTP_200_OK

        html = BeautifulSoup(response.text, features="html.parser")
        rows = html.find("tbody").find_all("tr")
        assert len(rows) == len(test_data["webhooks"])


@pytest.mark.asyncio
class TestGetWebhook:
    async def test_unauthorized(
        self,
        unauthorized_dashboard_assertions: HTTPXResponseAssertion,
        test_client_dashboard: httpx.AsyncClient,
        test_data: TestData,
    ):
        response = await test_client_dashboard.get(
            f"/webhooks/{test_data['webhooks']['all'].id}"
        )

        unauthorized_dashboard_assertions(response)

    @pytest.mark.authenticated_admin(mode="session")
    async def test_not_existing(
        self,
        test_client_dashboard: httpx.AsyncClient,
        not_existing_uuid: uuid.UUID,
    ):
        response = await test_client_dashboard.get(f"/webhooks/{not_existing_uuid}")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="aside")
    async def test_valid(
        self, test_client_dashboard: httpx.AsyncClient, test_data: TestData
    ):
        webhook = test_data["webhooks"]["all"]
        response = await test_client_dashboard.get(f"/webhooks/{webhook.id}")

        assert response.status_code == status.HTTP_200_OK

        html = BeautifulSoup(response.text, features="html.parser")
        title = html.find("h2")
        assert webhook.url in title.text


@pytest.mark.asyncio
class TestCreateWebhook:
    async def test_unauthorized(
        self,
        unauthorized_dashboard_assertions: HTTPXResponseAssertion,
        test_client_dashboard: httpx.AsyncClient,
    ):
        response = await test_client_dashboard.post("/webhooks/create", data={})

        unauthorized_dashboard_assertions(response)

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_invalid_event(
        self, test_client_dashboard: httpx.AsyncClient, csrf_token: str
    ):
        response = await test_client_dashboard.post(
            "/webhooks/create",
            data={
                "url": "https://internal.bretagne.duchy/webhook",
                "events": ["user.created", "invalid_event"],
                "csrf_token": csrf_token,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_valid(
        self,
        test_client_dashboard: httpx.AsyncClient,
        test_data: TestData,
        csrf_token: str,
        main_session: AsyncSession,
    ):
        response = await test_client_dashboard.post(
            "/webhooks/create",
            data={
                "url": "https://internal.bretagne.duchy/webhook",
                "events": ["user.created", "user.forgot_password_requested"],
                "csrf_token": csrf_token,
            },
        )

        assert response.status_code == status.HTTP_201_CREATED

        webhook_repository = WebhookRepository(main_session)
        webhook = await webhook_repository.get_by_id(
            uuid.UUID(response.headers["X-Fief-Object-Id"])
        )
        assert webhook is not None
        assert webhook.url == "https://internal.bretagne.duchy/webhook"
        assert webhook.events == ["user.created", "user.forgot_password_requested"]


@pytest.mark.asyncio
class TestUpdateWebhook:
    async def test_unauthorized(
        self,
        unauthorized_dashboard_assertions: HTTPXResponseAssertion,
        test_client_dashboard: httpx.AsyncClient,
        test_data: TestData,
    ):
        webhook = test_data["webhooks"]["all"]
        response = await test_client_dashboard.post(
            f"/webhooks/{webhook.id}/edit", data={}
        )

        unauthorized_dashboard_assertions(response)

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_not_existing(
        self,
        test_client_dashboard: httpx.AsyncClient,
        not_existing_uuid: uuid.UUID,
    ):
        response = await test_client_dashboard.post(
            f"/webhooks/{not_existing_uuid}/edit", data={}
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_invalid_event(
        self,
        test_client_dashboard: httpx.AsyncClient,
        test_data: TestData,
        csrf_token: str,
    ):
        webhook = test_data["webhooks"]["all"]
        response = await test_client_dashboard.post(
            f"/webhooks/{webhook.id}/edit",
            data={
                "url": webhook.url,
                "events": ["user.created", "invalid_event"],
                "csrf_token": csrf_token,
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_valid(
        self,
        test_client_dashboard: httpx.AsyncClient,
        test_data: TestData,
        csrf_token: str,
        main_session: AsyncSession,
    ):
        webhook = test_data["webhooks"]["all"]
        response = await test_client_dashboard.post(
            f"/webhooks/{webhook.id}/edit",
            data={
                "url": webhook.url,
                "events": ["user.created"],
                "csrf_token": csrf_token,
            },
        )

        assert response.status_code == status.HTTP_200_OK

        webhook_repository = WebhookRepository(main_session)
        updated_webhook = await webhook_repository.get_by_id(webhook.id)
        assert updated_webhook is not None
        assert updated_webhook.events == ["user.created"]


@pytest.mark.asyncio
class TestRegenerateWebhookSecret:
    async def test_unauthorized(
        self,
        unauthorized_dashboard_assertions: HTTPXResponseAssertion,
        test_client_dashboard: httpx.AsyncClient,
        test_data: TestData,
    ):
        webhook = test_data["webhooks"]["all"]
        response = await test_client_dashboard.post(f"/webhooks/{webhook.id}/secret")

        unauthorized_dashboard_assertions(response)

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_not_existing(
        self,
        test_client_dashboard: httpx.AsyncClient,
        not_existing_uuid: uuid.UUID,
    ):
        response = await test_client_dashboard.post(
            f"/webhooks/{not_existing_uuid}/secret"
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_success(
        self,
        test_client_dashboard: httpx.AsyncClient,
        test_data: TestData,
        main_session: AsyncSession,
    ):
        webhook = test_data["webhooks"]["all"]
        response = await test_client_dashboard.post(f"/webhooks/{webhook.id}/secret")

        assert response.status_code == status.HTTP_200_OK

        html = BeautifulSoup(response.text, features="html.parser")
        secret = html.find("pre").text

        webhook_repository = WebhookRepository(main_session)
        updated_webhook = await webhook_repository.get_by_id(webhook.id)
        assert updated_webhook is not None
        assert updated_webhook.secret == secret


@pytest.mark.asyncio
class TestDeleteWebhook:
    async def test_unauthorized(
        self,
        unauthorized_dashboard_assertions: HTTPXResponseAssertion,
        test_client_dashboard: httpx.AsyncClient,
        test_data: TestData,
    ):
        webhook = test_data["webhooks"]["all"]
        response = await test_client_dashboard.delete(f"/webhooks/{webhook.id}/delete")

        unauthorized_dashboard_assertions(response)

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_not_existing(
        self,
        test_client_dashboard: httpx.AsyncClient,
        not_existing_uuid: uuid.UUID,
    ):
        response = await test_client_dashboard.delete(
            f"/webhooks/{not_existing_uuid}/delete"
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_valid_get(
        self, test_client_dashboard: httpx.AsyncClient, test_data: TestData
    ):
        webhook = test_data["webhooks"]["all"]
        response = await test_client_dashboard.get(f"/webhooks/{webhook.id}/delete")

        assert response.status_code == status.HTTP_200_OK

        html = BeautifulSoup(response.text, features="html.parser")
        submit_button = html.find(
            "button",
            attrs={"hx-delete": f"http://api.fief.dev/webhooks/{webhook.id}/delete"},
        )
        assert submit_button is not None

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_valid_delete(
        self,
        test_client_dashboard: httpx.AsyncClient,
        test_data: TestData,
    ):
        webhook = test_data["webhooks"]["all"]
        response = await test_client_dashboard.delete(f"/webhooks/{webhook.id}/delete")

        assert response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.asyncio
class TestGetWebhookLogs:
    async def test_unauthorized(
        self,
        unauthorized_dashboard_assertions: HTTPXResponseAssertion,
        test_client_dashboard: httpx.AsyncClient,
        test_data: TestData,
    ):
        response = await test_client_dashboard.get(
            f"/webhooks/{test_data['webhooks']['all'].id}/logs"
        )

        unauthorized_dashboard_assertions(response)

    @pytest.mark.authenticated_admin(mode="session")
    async def test_not_existing(
        self,
        test_client_dashboard: httpx.AsyncClient,
        not_existing_uuid: uuid.UUID,
    ):
        response = await test_client_dashboard.get(
            f"/webhooks/{not_existing_uuid}/logs"
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="main")
    async def test_valid(
        self, test_client_dashboard: httpx.AsyncClient, test_data: TestData
    ):
        webhook = test_data["webhooks"]["all"]
        response = await test_client_dashboard.get(f"/webhooks/{webhook.id}/logs")

        assert response.status_code == status.HTTP_200_OK

        html = BeautifulSoup(response.text, features="html.parser")
        rows = html.find("tbody").find_all("tr")
        assert len(rows) == len(
            [
                log
                for log in test_data["webhook_logs"].values()
                if log.webhook_id == webhook.id
            ]
        )


@pytest.mark.asyncio
class TestGetWebhookLog:
    async def test_unauthorized(
        self,
        unauthorized_dashboard_assertions: HTTPXResponseAssertion,
        test_client_dashboard: httpx.AsyncClient,
        test_data: TestData,
    ):
        response = await test_client_dashboard.get(
            f"/webhooks/{test_data['webhooks']['all'].id}/logs/{test_data['webhook_logs']['all_log1'].id}"
        )

        unauthorized_dashboard_assertions(response)

    @pytest.mark.authenticated_admin(mode="session")
    async def test_not_existing_webhook(
        self,
        test_client_dashboard: httpx.AsyncClient,
        not_existing_uuid: uuid.UUID,
        test_data: TestData,
    ):
        response = await test_client_dashboard.get(
            f"/webhooks/{not_existing_uuid}/logs/{test_data['webhook_logs']['all_log1'].id}"
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.authenticated_admin(mode="session")
    async def test_not_existing_webhook_log(
        self,
        test_client_dashboard: httpx.AsyncClient,
        not_existing_uuid: uuid.UUID,
        test_data: TestData,
    ):
        response = await test_client_dashboard.get(
            f"/webhooks/{test_data['webhooks']['all'].id}/logs/{not_existing_uuid}"
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.authenticated_admin(mode="session")
    @pytest.mark.htmx(target="modal")
    async def test_valid(
        self, test_client_dashboard: httpx.AsyncClient, test_data: TestData
    ):
        webhook = test_data["webhooks"]["all"]
        webhook_log = test_data["webhook_logs"]["all_log1"]
        response = await test_client_dashboard.get(
            f"/webhooks/{webhook.id}/logs/{webhook_log.id}"
        )

        assert response.status_code == status.HTTP_200_OK
