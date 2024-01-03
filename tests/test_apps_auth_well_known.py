import httpx
import pytest
from fastapi import status
from jwcrypto import jwk

from fief.services.response_type import ALLOWED_RESPONSE_TYPES
from tests.types import TenantParams


@pytest.mark.asyncio
class TestWellKnownOpenIDConfiguration:
    @pytest.mark.parametrize("x_forwarded_host", [None, "proxy.bretagne.duchy"])
    async def test_return_configuration(
        self,
        x_forwarded_host: str | None,
        tenant_params: TenantParams,
        test_client_auth: httpx.AsyncClient,
    ):
        headers = {}
        if x_forwarded_host is not None:
            headers["X-Forwarded-Host"] = x_forwarded_host

        response = await test_client_auth.get(
            f"{tenant_params.path_prefix}/.well-known/openid-configuration",
            headers=headers,
        )

        assert response.status_code == status.HTTP_200_OK

        json = response.json()

        assert json["issuer"] == tenant_params.tenant.get_host()
        for key in json:
            assert json[key] is not None

        assert json["response_types_supported"] == ALLOWED_RESPONSE_TYPES
        assert json["token_endpoint_auth_methods_supported"] == [
            "client_secret_basic",
            "client_secret_post",
        ]
        assert json["code_challenge_methods_supported"] == ["plain", "S256"]

        endpoint: str = json["authorization_endpoint"]
        if x_forwarded_host is not None:
            assert endpoint.startswith(f"http://{x_forwarded_host}")
        else:
            assert endpoint.startswith("http://api.fief.dev")


@pytest.mark.asyncio
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

        key: jwk.JWK | None = keyset.get_key(tenant_params.tenant.get_sign_jwk()["kid"])
        assert key is not None
        assert key.has_private is False
