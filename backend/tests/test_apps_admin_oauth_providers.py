import uuid
from typing import Dict

import httpx
import pytest
from fastapi import status

from fief.db import AsyncSession
from fief.errors import APIErrorCode
from fief.repositories import OAuthProviderRepository
from tests.data import TestData


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestListOAuthProviders:
    async def test_unauthorized(self, test_client_admin: httpx.AsyncClient):
        response = await test_client_admin.get("/oauth-providers/")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.authenticated_admin
    async def test_valid(
        self, test_client_admin: httpx.AsyncClient, test_data: TestData
    ):
        response = await test_client_admin.get("/oauth-providers/")

        assert response.status_code == status.HTTP_200_OK

        json = response.json()
        assert json["count"] == len(test_data["oauth_providers"])


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestCreateOAuthProvider:
    async def test_unauthorized(self, test_client_admin: httpx.AsyncClient):
        response = await test_client_admin.post("/oauth-providers/", json={})

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.authenticated_admin
    async def test_missing_configuration_endpoint_for_openid(
        self, test_client_admin: httpx.AsyncClient
    ):
        response = await test_client_admin.post(
            "/oauth-providers/",
            json={
                "provider": "OPENID",
                "client_id": "CLIENT_ID",
                "client_secret": "CLIENT_SECRET",
                "scopes": ["openid"],
            },
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        json = response.json()
        assert (
            json["detail"][0]["msg"]
            == APIErrorCode.OAUTH_PROVIDER_MISSING_OPENID_CONFIGURATION_ENDPOINT
        )

    @pytest.mark.parametrize(
        "payload",
        [
            {"provider": "GOOGLE", "scopes": ["openid"]},
            {
                "provider": "OPENID",
                "openid_configuration_endpoint": "http://rome.city/.well-known/openid-configuration",
                "scopes": ["openid"],
            },
        ],
    )
    @pytest.mark.authenticated_admin
    async def test_valid(
        self,
        payload: Dict[str, str],
        test_client_admin: httpx.AsyncClient,
        workspace_session: AsyncSession,
    ):
        response = await test_client_admin.post(
            "/oauth-providers/",
            json={
                "client_id": "CLIENT_ID",
                "client_secret": "CLIENT_SECRET",
                **payload,
            },
        )

        assert response.status_code == status.HTTP_201_CREATED

        json = response.json()
        assert json["provider"] == payload["provider"]
        assert json["client_id"] == "**********"
        assert json["client_secret"] == "**********"

        repository = OAuthProviderRepository(workspace_session)
        oauth_provider = await repository.get_by_id(uuid.UUID(json["id"]))
        assert oauth_provider is not None
        assert oauth_provider.client_id == "CLIENT_ID"
        assert oauth_provider._client_id != "CLIENT_ID"
        assert oauth_provider.client_secret == "CLIENT_SECRET"
        assert oauth_provider._client_secret != "CLIENT_SECRET"


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestUpdateOAuthProvider:
    async def test_unauthorized(
        self, test_client_admin: httpx.AsyncClient, test_data: TestData
    ):
        oauth_provider = test_data["oauth_providers"]["google"]
        response = await test_client_admin.patch(
            f"/oauth-providers/{oauth_provider.id}", json={}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.authenticated_admin
    async def test_not_existing(
        self, test_client_admin: httpx.AsyncClient, not_existing_uuid: uuid.UUID
    ):
        response = await test_client_admin.patch(
            f"/oauth-providers/{not_existing_uuid}", json={}
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.authenticated_admin
    async def test_missing_configuration_endpoint_for_openid(
        self,
        test_client_admin: httpx.AsyncClient,
        test_data: TestData,
    ):
        oauth_provider = test_data["oauth_providers"]["openid"]

        response = await test_client_admin.patch(
            f"/oauth-providers/{oauth_provider.id}",
            json={"openid_configuration_endpoint": None},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        json = response.json()
        assert (
            json["detail"][0]["msg"]
            == APIErrorCode.OAUTH_PROVIDER_MISSING_OPENID_CONFIGURATION_ENDPOINT
        )

    @pytest.mark.authenticated_admin
    async def test_cant_update_provider(
        self, test_client_admin: httpx.AsyncClient, test_data: TestData
    ):
        oauth_provider = test_data["oauth_providers"]["google"]
        response = await test_client_admin.patch(
            f"/oauth-providers/{oauth_provider.id}", json={"provider": "GITHUB"}
        )

        assert response.status_code == status.HTTP_200_OK

        json = response.json()
        assert json["provider"] == "GOOGLE"

    @pytest.mark.authenticated_admin
    async def test_valid(
        self,
        test_client_admin: httpx.AsyncClient,
        test_data: TestData,
    ):
        oauth_provider = test_data["oauth_providers"]["openid"]
        response = await test_client_admin.patch(
            f"/oauth-providers/{oauth_provider.id}",
            json={
                "openid_configuration_endpoint": "http://rome.city/v2/.well-known/openid-configuration"
            },
        )

        assert response.status_code == status.HTTP_200_OK

        json = response.json()
        assert (
            json["openid_configuration_endpoint"]
            == "http://rome.city/v2/.well-known/openid-configuration"
        )


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestDeleteOAuthProvider:
    async def test_unauthorized(
        self, test_client_admin: httpx.AsyncClient, test_data: TestData
    ):
        oauth_provider = test_data["oauth_providers"]["google"]
        response = await test_client_admin.delete(
            f"/oauth-providers/{oauth_provider.id}"
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.authenticated_admin
    async def test_not_existing(
        self, test_client_admin: httpx.AsyncClient, not_existing_uuid: uuid.UUID
    ):
        response = await test_client_admin.delete(
            f"/oauth-providers/{not_existing_uuid}"
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.authenticated_admin
    async def test_valid(
        self, test_client_admin: httpx.AsyncClient, test_data: TestData
    ):
        oauth_provider = test_data["oauth_providers"]["google"]
        response = await test_client_admin.delete(
            f"/oauth-providers/{oauth_provider.id}"
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT
