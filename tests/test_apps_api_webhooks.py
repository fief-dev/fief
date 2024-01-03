import uuid

import httpx
import pytest
from fastapi import status

from tests.data import TestData
from tests.helpers import HTTPXResponseAssertion


@pytest.mark.asyncio
class TestListWebhooks:
    async def test_unauthorized(
        self,
        unauthorized_api_assertions: HTTPXResponseAssertion,
        test_client_api: httpx.AsyncClient,
    ):
        response = await test_client_api.get("/webhooks/")

        unauthorized_api_assertions(response)

    @pytest.mark.authenticated_admin
    async def test_valid(self, test_client_api: httpx.AsyncClient, test_data: TestData):
        response = await test_client_api.get("/webhooks/")

        assert response.status_code == status.HTTP_200_OK

        json = response.json()
        assert json["count"] == len(test_data["webhooks"])

        for webhook in json["results"]:
            assert "secret" not in webhook


@pytest.mark.asyncio
class TestGetWebhook:
    async def test_unauthorized(
        self,
        unauthorized_api_assertions: HTTPXResponseAssertion,
        test_client_api: httpx.AsyncClient,
        test_data: TestData,
    ):
        webhook = test_data["webhooks"]["all"]
        response = await test_client_api.get(f"/webhooks/{webhook.id}")

        unauthorized_api_assertions(response)

    @pytest.mark.authenticated_admin
    async def test_not_existing(
        self, test_client_api: httpx.AsyncClient, not_existing_uuid: uuid.UUID
    ):
        response = await test_client_api.get(f"/webhooks/{not_existing_uuid}")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.authenticated_admin
    async def test_valid(self, test_client_api: httpx.AsyncClient, test_data: TestData):
        webhook = test_data["webhooks"]["all"]
        response = await test_client_api.get(f"/webhooks/{webhook.id}")

        assert response.status_code == status.HTTP_200_OK

        json = response.json()
        assert "secret" not in json


@pytest.mark.asyncio
class TestCreateWebhook:
    async def test_unauthorized(
        self,
        unauthorized_api_assertions: HTTPXResponseAssertion,
        test_client_api: httpx.AsyncClient,
    ):
        response = await test_client_api.post("/webhooks/", json={})

        unauthorized_api_assertions(response)

    @pytest.mark.authenticated_admin
    async def test_invalid_event(self, test_client_api: httpx.AsyncClient):
        response = await test_client_api.post(
            "/webhooks/",
            json={
                "url": "https://internal.bretagne.duchy/webhook",
                "events": ["user.created", "invalid_event"],
            },
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        json = response.json()
        assert json["detail"][0]["loc"] == ["body", "events", 1]

    @pytest.mark.authenticated_admin
    async def test_valid(self, test_client_api: httpx.AsyncClient, test_data: TestData):
        response = await test_client_api.post(
            "/webhooks/",
            json={
                "url": "https://internal.bretagne.duchy/webhook",
                "events": ["user.created", "user.forgot_password_requested"],
            },
        )

        assert response.status_code == status.HTTP_201_CREATED

        json = response.json()
        assert json["url"] == "https://internal.bretagne.duchy/webhook"
        assert json["events"] == ["user.created", "user.forgot_password_requested"]
        assert "secret" in json


@pytest.mark.asyncio
class TestUpdateWebhook:
    async def test_unauthorized(
        self,
        unauthorized_api_assertions: HTTPXResponseAssertion,
        test_client_api: httpx.AsyncClient,
        test_data: TestData,
    ):
        webhook = test_data["webhooks"]["all"]
        response = await test_client_api.patch(f"/webhooks/{webhook.id}", json={})

        unauthorized_api_assertions(response)

    @pytest.mark.authenticated_admin
    async def test_not_existing(
        self, test_client_api: httpx.AsyncClient, not_existing_uuid: uuid.UUID
    ):
        response = await test_client_api.patch(
            f"/webhooks/{not_existing_uuid}", json={}
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.authenticated_admin
    async def test_invalid_event(
        self, test_client_api: httpx.AsyncClient, test_data: TestData
    ):
        webhook = test_data["webhooks"]["all"]
        response = await test_client_api.patch(
            f"/webhooks/{webhook.id}",
            json={"events": ["user.created", "invalid_event"]},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        json = response.json()
        assert json["detail"][0]["loc"] == ["body", "events", 1]

    @pytest.mark.authenticated_admin
    async def test_valid(self, test_client_api: httpx.AsyncClient, test_data: TestData):
        webhook = test_data["webhooks"]["all"]
        response = await test_client_api.patch(
            f"/webhooks/{webhook.id}",
            json={"events": ["user.created"]},
        )

        assert response.status_code == status.HTTP_200_OK

        json = response.json()
        assert json["events"] == ["user.created"]
        assert "secret" not in json


@pytest.mark.asyncio
class TestRegenerateWebhookSecret:
    async def test_unauthorized(
        self,
        unauthorized_api_assertions: HTTPXResponseAssertion,
        test_client_api: httpx.AsyncClient,
        test_data: TestData,
    ):
        webhook = test_data["webhooks"]["all"]
        response = await test_client_api.post(f"/webhooks/{webhook.id}/secret")

        unauthorized_api_assertions(response)

    @pytest.mark.authenticated_admin
    async def test_success(
        self, test_client_api: httpx.AsyncClient, test_data: TestData
    ):
        webhook = test_data["webhooks"]["all"]
        response = await test_client_api.post(f"/webhooks/{webhook.id}/secret")

        assert response.status_code == status.HTTP_200_OK

        json = response.json()
        assert "secret" in json


@pytest.mark.asyncio
class TestDeleteWebhook:
    async def test_unauthorized(
        self,
        unauthorized_api_assertions: HTTPXResponseAssertion,
        test_client_api: httpx.AsyncClient,
        test_data: TestData,
    ):
        webhook = test_data["webhooks"]["all"]
        response = await test_client_api.delete(f"/webhooks/{webhook.id}")

        unauthorized_api_assertions(response)

    @pytest.mark.authenticated_admin
    async def test_not_existing(
        self, test_client_api: httpx.AsyncClient, not_existing_uuid: uuid.UUID
    ):
        response = await test_client_api.delete(f"/webhooks/{not_existing_uuid}")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.authenticated_admin
    async def test_valid(self, test_client_api: httpx.AsyncClient, test_data: TestData):
        webhook = test_data["webhooks"]["all"]
        response = await test_client_api.delete(f"/webhooks/{webhook.id}")

        assert response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.asyncio
class TestListWebhookLogs:
    async def test_unauthorized(
        self,
        unauthorized_api_assertions: HTTPXResponseAssertion,
        test_client_api: httpx.AsyncClient,
        test_data: TestData,
    ):
        webhook = test_data["webhooks"]["all"]
        response = await test_client_api.get(f"/webhooks/{webhook.id}/logs")

        unauthorized_api_assertions(response)

    @pytest.mark.authenticated_admin
    async def test_not_existing(
        self, test_client_api: httpx.AsyncClient, not_existing_uuid: uuid.UUID
    ):
        response = await test_client_api.get(f"/webhooks/{not_existing_uuid}/logs")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.authenticated_admin
    async def test_valid(self, test_client_api: httpx.AsyncClient, test_data: TestData):
        webhook = test_data["webhooks"]["all"]
        response = await test_client_api.get(f"/webhooks/{webhook.id}/logs")

        assert response.status_code == status.HTTP_200_OK

        json = response.json()
        assert json["count"] == len(
            [
                log
                for log in test_data["webhook_logs"].values()
                if log.webhook_id == webhook.id
            ]
        )
