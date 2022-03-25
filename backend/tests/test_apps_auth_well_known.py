from typing import Optional

import httpx
import pytest
from fastapi import status
from jwcrypto import jwk

from fief.models import Workspace
from tests.conftest import TenantParams


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestWellKnownOpenIDConfiguration:
    async def test_return_configuration(
        self,
        workspace: Workspace,
        tenant_params: TenantParams,
        test_client_auth: httpx.AsyncClient,
    ):
        response = await test_client_auth.get(
            f"{tenant_params.path_prefix}/.well-known/openid-configuration"
        )

        assert response.status_code == status.HTTP_200_OK

        json = response.json()

        assert json["issuer"] == tenant_params.tenant.get_host(workspace.domain)
        for key in json:
            assert json[key] is not None

        assert json["token_endpoint_auth_methods_supported"] == [
            "client_secret_basic",
            "client_secret_post",
        ]


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestWellKnownJWKS:
    async def test_return_public_keys(
        self,
        tenant_params: TenantParams,
        test_client_auth: httpx.AsyncClient,
    ):
        response = await test_client_auth.get(
            f"{tenant_params.path_prefix}/.well-known/jwks.json"
        )

        assert response.status_code == status.HTTP_200_OK

        keyset = jwk.JWKSet.from_json(response.text)

        key: Optional[jwk.JWK] = keyset.get_key(
            tenant_params.tenant.get_sign_jwk()["kid"]
        )
        assert key is not None
        assert key.has_private is False
