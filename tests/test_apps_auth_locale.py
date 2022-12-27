import httpx
import pytest
from bs4 import BeautifulSoup
from fastapi import status

from fief.settings import settings
from tests.data import TestData


@pytest.mark.asyncio
@pytest.mark.workspace_host
async def test_switch_language(
    test_client_auth: httpx.AsyncClient, test_data: TestData
):
    login_session = test_data["login_sessions"]["default"]
    client = login_session.client
    tenant = client.tenant
    path_prefix = tenant.slug if not tenant.default else ""

    cookies = {}
    cookies[settings.login_session_cookie_name] = login_session.token

    response = await test_client_auth.get(
        f"{path_prefix}/register", cookies=cookies, headers={"accept-language": "en-US"}
    )

    assert response.status_code == status.HTTP_200_OK

    html = BeautifulSoup(response.text, features="html.parser")
    assert html.find("label", attrs={"for": "email"}).text.strip() == "Email address\n*"

    response = await test_client_auth.get(
        f"{path_prefix}/register", cookies=cookies, headers={"accept-language": "fr-FR"}
    )

    assert response.status_code == status.HTTP_200_OK

    html = BeautifulSoup(response.text, features="html.parser")
    assert (
        html.find("label", attrs={"for": "email"}).text.strip() == "Adresse e-mail\n*"
    )
