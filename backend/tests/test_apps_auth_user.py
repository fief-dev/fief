from typing import Optional

import httpx
import pytest
from fastapi import status

from tests.types import TenantParams


@pytest.mark.asyncio
@pytest.mark.workspace_host
@pytest.mark.parametrize("method", ["GET", "POST"])
class TestUserUserinfo:
    @pytest.mark.parametrize(
        "authorization",
        [
            None,
            "INVALID_FORMAT",
            "INVALID_SCHEMA INVALID_TOKEN",
            "Bearer INVALID_TOKEN",
        ],
    )
    async def test_unauthorized(
        self,
        method: str,
        authorization: Optional[str],
        tenant_params: TenantParams,
        test_client_auth: httpx.AsyncClient,
    ):
        headers = {}
        if authorization is not None:
            headers["Authorization"] = authorization

        response = await test_client_auth.request(
            method, f"{tenant_params.path_prefix}/api/userinfo", headers=headers
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.access_token(from_tenant_params=True)
    async def test_authorized(
        self,
        method: str,
        tenant_params: TenantParams,
        test_client_auth: httpx.AsyncClient,
    ):
        response = await test_client_auth.request(
            method, f"{tenant_params.path_prefix}/api/userinfo"
        )

        assert response.status_code == status.HTTP_200_OK

        user = tenant_params.user

        json = response.json()
        assert json == {
            "sub": str(user.id),
            "email": user.email,
            "tenant_id": str(user.tenant_id),
        }
