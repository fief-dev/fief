from typing import AsyncGenerator, List, Optional

import httpx
import pytest
from fastapi import Depends, FastAPI, status

from fief.dependencies.locale import get_accepted_languages
from fief.locale import get_preferred_locale
from tests.conftest import TestClientGeneratorType


@pytest.fixture
def app() -> FastAPI:
    app = FastAPI()

    @app.get("/locale")
    async def locale(
        languages: List[str] = Depends(get_accepted_languages),
    ):
        return {"locale": get_preferred_locale(languages)}

    return app


@pytest.fixture
@pytest.mark.asyncio
async def test_client(
    test_client_auth_generator: TestClientGeneratorType, app: FastAPI
) -> AsyncGenerator[httpx.AsyncClient, None]:
    async with test_client_auth_generator(app) as test_client:
        yield test_client


@pytest.mark.parametrize(
    "accept,expected",
    [
        pytest.param(None, "en_US", id="No accept-language header"),
        pytest.param(
            "fr-FR;q=0.9,en-US;q=0.8,en;q=0.7", "fr_FR", id="French preferred"
        ),
        pytest.param(
            "fr-FR;q=0.8,en-US;q=0.9,en;q=0.7",
            "en_US",
            id="English preferred not sorted",
        ),
        pytest.param("fr;q=0.9", "fr", id="Language only"),
        pytest.param("fr,en", "fr", id="No quality"),
        pytest.param("fr-ZZ;q=0.9", "fr", id="Unsupported territory"),
        pytest.param("eo;q=0.9", "en_US", id="Unsupported language"),
    ],
)
async def test_get_locale(
    accept: Optional[str], expected: str, test_client: httpx.AsyncClient
):
    headers = {}
    if accept is not None:
        headers["Accept-Language"] = accept
    response = await test_client.get("/locale", headers=headers)

    assert response.status_code == status.HTTP_200_OK

    json = response.json()
    assert json["locale"] == expected
