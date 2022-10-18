import uuid
from datetime import datetime, timedelta, timezone
from typing import Dict, Type
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
from fastapi import status
from httpx_oauth.oauth2 import (
    BaseOAuth2,
    OAuth2Error,
    RefreshTokenError,
    RefreshTokenNotSupportedError,
)
from pytest_mock import MockerFixture

from fief.db import AsyncSession
from fief.errors import APIErrorCode
from fief.repositories import OAuthAccountRepository, OAuthProviderRepository
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
        assert oauth_provider.client_secret == "CLIENT_SECRET"


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


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestGetOAuthProviderUserAccessToken:
    async def test_unauthorized(
        self, test_client_admin: httpx.AsyncClient, test_data: TestData
    ):
        oauth_provider = test_data["oauth_providers"]["google"]
        user = test_data["users"]["regular"]
        response = await test_client_admin.get(
            f"/oauth-providers/{oauth_provider.id}/access-token/{user.id}"
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.authenticated_admin
    async def test_not_existing_oauth_provider(
        self,
        test_client_admin: httpx.AsyncClient,
        test_data: TestData,
        not_existing_uuid: uuid.UUID,
    ):
        user = test_data["users"]["regular"]
        response = await test_client_admin.get(
            f"/oauth-providers/{not_existing_uuid}/access-token/{user.id}"
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.authenticated_admin
    async def test_not_existing_user(
        self,
        test_client_admin: httpx.AsyncClient,
        test_data: TestData,
        not_existing_uuid: uuid.UUID,
    ):
        oauth_provider = test_data["oauth_providers"]["google"]
        response = await test_client_admin.get(
            f"/oauth-providers/{oauth_provider.id}/access-token/{not_existing_uuid}"
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.authenticated_admin
    async def test_no_associated_oauth_account(
        self, test_client_admin: httpx.AsyncClient, test_data: TestData
    ):
        oauth_provider = test_data["oauth_providers"]["google"]
        user = test_data["users"]["regular_secondary"]
        response = await test_client_admin.get(
            f"/oauth-providers/{oauth_provider.id}/access-token/{user.id}"
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.authenticated_admin
    async def test_valid_fresh_token(
        self, test_client_admin: httpx.AsyncClient, test_data: TestData
    ):
        oauth_provider = test_data["oauth_providers"]["google"]
        user = test_data["users"]["regular"]
        response = await test_client_admin.get(
            f"/oauth-providers/{oauth_provider.id}/access-token/{user.id}"
        )

        assert response.status_code == status.HTTP_200_OK

        oauth_account = test_data["oauth_accounts"]["regular_google"]

        json = response.json()
        assert json["id"] == str(oauth_account.id)
        assert json["account_id"] == str(oauth_account.account_id)
        assert json["access_token"] == oauth_account.access_token
        assert "expires_at" in json

    @pytest.mark.parametrize(
        "exception,error_code",
        [
            (
                RefreshTokenNotSupportedError,
                APIErrorCode.OAUTH_PROVIDER_REFRESH_TOKEN_NOT_SUPPORTED,
            ),
            (RefreshTokenError, APIErrorCode.OAUTH_PROVIDER_REFRESH_TOKEN_ERROR),
        ],
    )
    @pytest.mark.authenticated_admin
    async def test_expired_token_refresh_error(
        self,
        exception: Type[OAuth2Error],
        error_code: APIErrorCode,
        mocker: MockerFixture,
        test_client_admin: httpx.AsyncClient,
        test_data: TestData,
    ):
        oauth_provider_service_mock = MagicMock(spec=BaseOAuth2)
        oauth_provider_service_mock.refresh_token.side_effect = exception()
        mocker.patch(
            "fief.apps.admin.routers.oauth_providers.get_oauth_provider_service"
        ).return_value = oauth_provider_service_mock

        oauth_provider = test_data["oauth_providers"]["openid"]
        user = test_data["users"]["regular"]
        response = await test_client_admin.get(
            f"/oauth-providers/{oauth_provider.id}/access-token/{user.id}"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        json = response.json()
        assert json["detail"] == error_code

    @pytest.mark.authenticated_admin
    async def test_valid_expired_token(
        self,
        mocker: MockerFixture,
        test_client_admin: httpx.AsyncClient,
        test_data: TestData,
        workspace_session: AsyncSession,
    ):
        oauth_provider_service_mock = MagicMock(spec=BaseOAuth2)
        expires_at = datetime.now(timezone.utc).replace(microsecond=0) + timedelta(
            seconds=3600
        )
        oauth_provider_service_mock.refresh_token.side_effect = AsyncMock(
            return_value={
                "access_token": "REFRESHED_ACCESS_TOKEN",
                "expires_in": 3600,
                "expires_at": int(expires_at.timestamp()),
            }
        )
        mocker.patch(
            "fief.apps.admin.routers.oauth_providers.get_oauth_provider_service"
        ).return_value = oauth_provider_service_mock

        oauth_provider = test_data["oauth_providers"]["openid"]
        user = test_data["users"]["regular"]
        response = await test_client_admin.get(
            f"/oauth-providers/{oauth_provider.id}/access-token/{user.id}"
        )

        assert response.status_code == status.HTTP_200_OK

        oauth_account = test_data["oauth_accounts"]["regular_openid_expired"]

        json = response.json()
        assert json["id"] == str(oauth_account.id)
        assert json["account_id"] == str(oauth_account.account_id)
        assert json["access_token"] == "REFRESHED_ACCESS_TOKEN"
        assert "expires_at" in json

        oauth_account_repository = OAuthAccountRepository(workspace_session)
        updated_oauth_account = await oauth_account_repository.get_by_id(
            oauth_account.id
        )
        assert updated_oauth_account is not None
        assert updated_oauth_account.access_token == "REFRESHED_ACCESS_TOKEN"
        assert updated_oauth_account.expires_at == expires_at
