import httpx
import pytest
from fastapi import status

from tests.conftest import TenantParams
from tests.helpers import security_headers_assertions


@pytest.mark.asyncio
async def test_admin_app(test_client_api: httpx.AsyncClient):
    response = await test_client_api.get("/openapi.json")

    assert response.status_code == status.HTTP_200_OK
    security_headers_assertions(response)


@pytest.mark.asyncio
@pytest.mark.authenticated_admin(mode="session")
async def test_dashboard_app(test_client_dashboard: httpx.AsyncClient):
    response = await test_client_dashboard.get("/")

    assert response.status_code == status.HTTP_200_OK
    security_headers_assertions(response)


@pytest.mark.asyncio
async def test_auth_app(
    tenant_params: TenantParams, test_client_auth: httpx.AsyncClient
):
    response = await test_client_auth.get(
        f"{tenant_params.path_prefix}/.well-known/jwks.json"
    )

    assert response.status_code == status.HTTP_200_OK
    security_headers_assertions(response)
