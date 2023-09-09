import httpx
import pytest
from fastapi import status

from fief.settings import settings
from tests.types import TenantParams


@pytest.mark.asyncio
@pytest.mark.workspace_host
@pytest.mark.parametrize(
    "path,cors_enabled",
    [
        ("/api/userinfo", True),
        ("/.well-known/openid-configuration", True),
        ("/authorize", False),
    ],
)
async def test_apps_auth_cors_configuration(
    path: str,
    cors_enabled: bool,
    tenant_params: TenantParams,
    test_client_auth: httpx.AsyncClient,
):
    response = await test_client_auth.options(
        f"{tenant_params.path_prefix}{path}",
        headers={"access-control-request-method": "GET", "origin": "bretagne.duchy"},
    )

    if cors_enabled:
        assert response.status_code == status.HTTP_200_OK
        assert response.headers.get("Access-Control-Allow-Origin") == "*"
    else:
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.asyncio
@pytest.mark.workspace_host
@pytest.mark.parametrize("locale", ["foo_BAR", "en_HR", "en-HR"])
async def test_invalid_locale_cookie(
    locale: str, tenant_params: TenantParams, test_client_auth: httpx.AsyncClient
):
    response = await test_client_auth.get(
        f"{tenant_params.path_prefix}/.well-known/openid-configuration",
        cookies={settings.user_locale_cookie_name: locale},
    )

    assert response.status_code == status.HTTP_200_OK
