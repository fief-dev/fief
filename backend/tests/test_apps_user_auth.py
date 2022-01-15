import httpx
import pytest
from fastapi import status
from fastapi_users.router.common import ErrorCode as FastAPIUsersErrorCode
from furl import furl
from pytest_lazyfixture import lazy_fixture

from fief.errors import ErrorCode
from fief.models import AuthorizationCode
from tests.data import TestData


@pytest.mark.asyncio
@pytest.mark.test_data
@pytest.mark.account_host
class TestAuthAuthorize:
    async def test_missing_parameters(self, test_client_user: httpx.AsyncClient):
        response = await test_client_user.get("/auth/authorize")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_unknown_client_id(self, test_client_user: httpx.AsyncClient):
        response = await test_client_user.get(
            "/auth/authorize",
            params={
                "response_type": "code",
                "client_id": "UNKNOWN",
                "redirect_uri": "https://bretagne.duchy/callback",
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        json = response.json()
        assert json["detail"] == ErrorCode.AUTH_INVALID_CLIENT_ID

    async def test_valid_client_id(
        self, test_client_user: httpx.AsyncClient, test_data: TestData
    ):
        client = test_data["clients"]["default_tenant"]
        tenant = client.tenant

        response = await test_client_user.get(
            "/auth/authorize",
            params={
                "response_type": "code",
                "client_id": client.client_id,
                "redirect_uri": "https://bretagne.duchy/callback",
            },
        )

        assert response.status_code == status.HTTP_200_OK

        json = response.json()
        assert json["parameters"] == {
            "response_type": "code",
            "client_id": client.client_id,
            "redirect_uri": "https://bretagne.duchy/callback",
            "scope": None,
            "state": None,
        }
        assert json["tenant"]["id"] == str(tenant.id)


@pytest.mark.asyncio
@pytest.mark.test_data
@pytest.mark.account_host
class TestAuthLogin:
    async def test_missing_parameters(self, test_client_user: httpx.AsyncClient):
        response = await test_client_user.post("/auth/login")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    async def test_bad_credentials(
        self, test_client_user: httpx.AsyncClient, test_data: TestData
    ):
        client = test_data["clients"]["default_tenant"]

        response = await test_client_user.post(
            "/auth/login",
            data={
                "response_type": "code",
                "client_id": client.client_id,
                "redirect_uri": "https://bretagne.duchy/callback",
                "username": "anne@bretagne.duchy",
                "password": "foo",
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        json = response.json()
        assert json["detail"] == FastAPIUsersErrorCode.LOGIN_BAD_CREDENTIALS

    async def test_valid_credentials(
        self, test_client_user: httpx.AsyncClient, test_data: TestData
    ):
        client = test_data["clients"]["default_tenant"]

        response = await test_client_user.post(
            "/auth/login",
            data={
                "response_type": "code",
                "client_id": client.client_id,
                "redirect_uri": "https://bretagne.duchy/callback",
                "state": "STATE",
                "username": "anne@bretagne.duchy",
                "password": "hermine",
            },
        )

        assert response.status_code == status.HTTP_200_OK

        json = response.json()
        redirect_uri = json["redirect_uri"]

        assert redirect_uri.startswith("https://bretagne.duchy/callback")
        parsed_location = furl(redirect_uri)
        assert "code" in parsed_location.query.params
        assert parsed_location.query.params["state"] == "STATE"

    async def test_none_state_not_in_redirect_uri(
        self, test_client_user: httpx.AsyncClient, test_data: TestData
    ):
        client = test_data["clients"]["default_tenant"]

        response = await test_client_user.post(
            "/auth/login",
            data={
                "response_type": "code",
                "client_id": client.client_id,
                "redirect_uri": "https://bretagne.duchy/callback",
                "username": "anne@bretagne.duchy",
                "password": "hermine",
            },
        )

        assert response.status_code == status.HTTP_200_OK

        json = response.json()
        redirect_uri = json["redirect_uri"]

        parsed_location = furl(redirect_uri)
        assert "state" not in parsed_location.query.params


@pytest.fixture
def authorization_code(test_data: TestData):
    return test_data["authorization_codes"]["default_regular"]


@pytest.fixture
def authorization_code_code(authorization_code: AuthorizationCode) -> str:
    return authorization_code.code


@pytest.fixture
def authorization_code_redirect_uri(authorization_code: AuthorizationCode) -> str:
    return authorization_code.redirect_uri


@pytest.fixture
def authorization_code_client_id(authorization_code: AuthorizationCode) -> str:
    return authorization_code.client.client_id


@pytest.fixture
def authorization_code_client_secret(authorization_code: AuthorizationCode) -> str:
    return authorization_code.client.client_secret


@pytest.mark.asyncio
@pytest.mark.test_data
@pytest.mark.account_host
class TestAuthToken:
    async def test_missing_parameters(self, test_client_user: httpx.AsyncClient):
        response = await test_client_user.post("/auth/token")

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.parametrize(
        "code,redirect_uri,client_id,client_secret,status,error_code",
        [
            (
                "INVALID_CODE",
                lazy_fixture("authorization_code_redirect_uri"),
                lazy_fixture("authorization_code_client_id"),
                lazy_fixture("authorization_code_client_secret"),
                status.HTTP_400_BAD_REQUEST,
                ErrorCode.AUTH_INVALID_AUTHORIZATION_CODE,
            ),
            (
                lazy_fixture("authorization_code_code"),
                lazy_fixture("authorization_code_redirect_uri"),
                "INVALID_CLIENT_ID",
                lazy_fixture("authorization_code_client_secret"),
                status.HTTP_400_BAD_REQUEST,
                ErrorCode.AUTH_INVALID_CLIENT_ID_SECRET,
            ),
            (
                lazy_fixture("authorization_code_code"),
                lazy_fixture("authorization_code_redirect_uri"),
                lazy_fixture("authorization_code_client_id"),
                "INVALID_CLIENT_SECRET",
                status.HTTP_400_BAD_REQUEST,
                ErrorCode.AUTH_INVALID_CLIENT_ID_SECRET,
            ),
            (
                lazy_fixture("authorization_code_code"),
                "https://bretagne.duchy/wrong-callback",
                lazy_fixture("authorization_code_client_id"),
                lazy_fixture("authorization_code_client_secret"),
                status.HTTP_400_BAD_REQUEST,
                ErrorCode.AUTH_REDIRECT_URI_MISMATCH,
            ),
        ],
    )
    async def test_invalid(
        self,
        test_client_user: httpx.AsyncClient,
        code: str,
        redirect_uri: str,
        client_id: str,
        client_secret: str,
        status: int,
        error_code: ErrorCode,
    ):
        response = await test_client_user.post(
            "/auth/token",
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": redirect_uri,
                "client_id": client_id,
                "client_secret": client_secret,
            },
        )

        assert response.status_code == status

        json = response.json()
        assert json["detail"] == error_code.value

    async def test_valid(
        self,
        test_client_user: httpx.AsyncClient,
        authorization_code: AuthorizationCode,
    ):
        response = await test_client_user.post(
            "/auth/token",
            data={
                "grant_type": "authorization_code",
                "code": authorization_code.code,
                "redirect_uri": authorization_code.redirect_uri,
                "client_id": authorization_code.client.client_id,
                "client_secret": authorization_code.client.client_secret,
            },
        )

        assert response.status_code == status.HTTP_200_OK

        json = response.json()
        assert isinstance(json["access_token"], str)
        assert isinstance(json["id_token"], str)
        assert json["token_type"] == "bearer"
