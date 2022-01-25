import httpx
import pytest
from fastapi import status
from jwcrypto import jwk

from fief.db import AsyncSession
from fief.managers import TenantManager
from tests.conftest import TenantParams


@pytest.mark.asyncio
@pytest.mark.test_data
@pytest.mark.account_host
class TestCreateEncryptionKey:
    async def test_success(
        self,
        test_client_admin: httpx.AsyncClient,
        tenant_params: TenantParams,
        account_session: AsyncSession,
    ):
        response = await test_client_admin.post(
            f"{tenant_params.path_prefix}/encryption-keys/"
        )

        assert response.status_code == status.HTTP_201_CREATED

        key = jwk.JWK.from_json(response.text)

        assert key.has_private == True
        assert key.has_public == True

        tenant = tenant_params.tenant

        manager = TenantManager(account_session)
        updated_tenant = await manager.get_by_id(tenant.id)
        assert updated_tenant is not None
        assert updated_tenant.encrypt_jwk is not None

        tenant_key = jwk.JWK.from_json(updated_tenant.encrypt_jwk)
        assert tenant_key.has_private == False
        assert tenant_key.has_public == True
