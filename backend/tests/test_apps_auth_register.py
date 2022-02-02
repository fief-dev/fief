from typing import Dict

import httpx
import pytest
from fastapi import status

from tests.conftest import TenantParams
from tests.data import TestData


@pytest.mark.asyncio
@pytest.mark.account_host
class TestGetRegister:
    async def test_page_render(
        self, tenant_params: TenantParams, test_client_auth: httpx.AsyncClient
    ):
        response = await test_client_auth.get(f"{tenant_params.path_prefix}/register")

        assert response.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
@pytest.mark.account_host
class TestPostRegister:
    @pytest.mark.parametrize(
        "data",
        [
            pytest.param({}, id="Missing email and password"),
            pytest.param({"email": "anne@bretagne.duchy"}, id="Missing password"),
            pytest.param({"password": "hermine1"}, id="Missing email"),
            pytest.param({"email": "anne", "password": "hermine1"}, id="Invalid email"),
            pytest.param(
                {"email": "anne@bretagne.duchy", "password": "h"}, id="Invalid password"
            ),
        ],
    )
    async def test_invalid_form(
        self,
        data: Dict[str, str],
        tenant_params: TenantParams,
        test_client_auth: httpx.AsyncClient,
    ):
        response = await test_client_auth.post(
            f"{tenant_params.path_prefix}/register", data=data
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    async def test_existing_user(self, test_client_auth: httpx.AsyncClient):
        response = await test_client_auth.post(
            "/register", data={"email": "anne@bretagne.duchy", "password": "hermine1"}
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        headers = response.headers
        assert headers["X-Fief-Error"] == "REGISTER_USER_ALREADY_EXISTS"

    async def test_new_user(self, test_client_auth: httpx.AsyncClient):
        response = await test_client_auth.post(
            "/register", data={"email": "louis@bretagne.duchy", "password": "hermine1"}
        )

        print(response.headers)

        assert response.status_code == status.HTTP_302_FOUND

    async def test_no_email_conflict_on_another_tenant(
        self, test_client_auth: httpx.AsyncClient, test_data: TestData
    ):
        response = await test_client_auth.post(
            f"/{test_data['tenants']['secondary'].slug}/register",
            data={"email": "anne@bretagne.duchy", "password": "hermine1"},
        )

        assert response.status_code == status.HTTP_302_FOUND
