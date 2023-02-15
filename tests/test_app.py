from collections.abc import AsyncGenerator

import httpx
import pytest
import pytest_asyncio
from fastapi import status

from fief.app import app
from tests.conftest import HTTPClientGeneratorType


@pytest_asyncio.fixture
async def test_client_app(
    test_client_generator: HTTPClientGeneratorType,
) -> AsyncGenerator[httpx.AsyncClient, None]:
    async with test_client_generator(app) as test_client:
        yield test_client


@pytest.mark.asyncio
async def test_admin_trailing_slash_redirection_(test_client_app: httpx.AsyncClient):
    response = await test_client_app.get("/admin")

    assert response.status_code == status.HTTP_308_PERMANENT_REDIRECT
    assert response.headers["location"] == "/admin/"
