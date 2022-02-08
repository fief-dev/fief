from typing import AsyncGenerator, Optional

import httpx
import pytest
from fastapi import Depends, FastAPI, status

from fief.dependencies.locale import get_translations
from fief.locale import Translations
from tests.conftest import TestClientGeneratorType


@pytest.fixture
def app() -> FastAPI:
    app = FastAPI()

    @app.get("/translations")
    async def translations(
        translations: Translations = Depends(get_translations),
    ):
        return {"language": translations.info()["language"]}

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
        pytest.param("fr;q=0.9", "fr_FR", id="Language only"),
        pytest.param("fr,en", "fr_FR", id="No quality"),
        pytest.param("fr-ZZ;q=0.9", "fr_FR", id="Unsupported territory"),
        pytest.param("eo;q=0.9", "en_US", id="Unsupported language"),
    ],
)
async def test_get_translations(
    accept: Optional[str], expected: str, test_client: httpx.AsyncClient
):
    headers = {}
    if accept is not None:
        headers["Accept-Language"] = accept
    response = await test_client.get("/translations", headers=headers)

    assert response.status_code == status.HTTP_200_OK

    json = response.json()
    assert json["language"] == expected
