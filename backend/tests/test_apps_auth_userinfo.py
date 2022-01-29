import httpx
import pytest
from fastapi import status

from tests.conftest import TenantParams
from tests.data import TestData


@pytest.mark.asyncio
@pytest.mark.account_host
class TestUserUserinfo:
    async def test_unauthorized(
        self, tenant_params: TenantParams, test_client_auth: httpx.AsyncClient
    ):
        response = await test_client_auth.get(f"{tenant_params.path_prefix}/userinfo")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.access_token(from_tenant_params=True)
    async def test_authorized(
        self, tenant_params: TenantParams, test_client_auth: httpx.AsyncClient
    ):
        response = await test_client_auth.get(f"{tenant_params.path_prefix}/userinfo")

        assert response.status_code == status.HTTP_200_OK

        user = tenant_params.user

        json = response.json()
        assert json == {
            "sub": str(user.id),
            "email": user.email,
            "tenant_id": str(user.tenant_id),
        }
