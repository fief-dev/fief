from typing import Optional

import httpx
import pytest
from fastapi import status
from jwcrypto import jwk

from fief.models import Account


@pytest.mark.asyncio
@pytest.mark.test_data
@pytest.mark.account_host
class TestWellKnownJWKS:
    async def test_return_public_keys(
        self, test_client_auth: httpx.AsyncClient, account: Account
    ):
        response = await test_client_auth.get("/.well-known/jwks.json")

        assert response.status_code == status.HTTP_200_OK

        keyset = jwk.JWKSet.from_json(response.text)

        key: Optional[jwk.JWK] = keyset.get_key(account.get_sign_jwk()["kid"])
        assert key is not None
        assert key.has_private is False
