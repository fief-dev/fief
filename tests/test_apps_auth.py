import httpx
import pytest
from fastapi import status

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
