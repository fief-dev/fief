import uuid
from typing import Any
from unittest.mock import MagicMock

import httpx
import pytest
from fastapi import status

from fief.db import AsyncSession
from fief.errors import APIErrorCode
from fief.models import User, Workspace
from fief.repositories import UserPermissionRepository, UserRoleRepository
from fief.tasks import on_after_register, on_user_role_created, on_user_role_deleted
from tests.data import TestData, tenants, users
from tests.helpers import HTTPXResponseAssertion


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestListUsers:
    async def test_unauthorized(
        self,
        unauthorized_api_assertions: HTTPXResponseAssertion,
        test_client_api: httpx.AsyncClient,
    ):
        response = await test_client_api.get("/users/")

        unauthorized_api_assertions(response)

    @pytest.mark.parametrize(
        "ordering", ["unknown_field", "email,-unknown_field", "tenant", "tenant.name"]
    )
    @pytest.mark.authenticated_admin
    async def test_unknown_ordering_field(
        self, ordering: str, test_client_api: httpx.AsyncClient
    ):
        response = await test_client_api.get("/users/", params={"ordering": ordering})

        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.authenticated_admin
    async def test_valid(self, test_client_api: httpx.AsyncClient, test_data: TestData):
        response = await test_client_api.get("/users/")

        assert response.status_code == status.HTTP_200_OK

        json = response.json()
        assert json["count"] == len(test_data["users"])

        for result in json["results"]:
            assert "tenant" in result

    @pytest.mark.parametrize(
        "params,results",
        [
            pytest.param(
                {"query": "ANNE"},
                [users["regular"], users["regular_secondary"]],
                id="Query filter",
            ),
            pytest.param(
                {"email": users["regular"].email}, [users["regular"]], id="Email filter"
            ),
            pytest.param(
                {"tenant": tenants["secondary"].id},
                [users["regular_secondary"]],
                id="Tenant filter",
            ),
            pytest.param(
                {"email": users["regular"].email, "tenant": tenants["secondary"].id},
                [],
                id="Email and tenant filter",
            ),
        ],
    )
    @pytest.mark.authenticated_admin
    async def test_query_filters(
        self,
        params: dict[str, Any],
        results: list[User],
        test_client_api: httpx.AsyncClient,
    ):
        response = await test_client_api.get("/users/", params=params)

        assert response.status_code == status.HTTP_200_OK

        json = response.json()
        assert json["count"] == len(results)

        assert set([uuid.UUID(result["id"]) for result in json["results"]]) == set(
            [result.id for result in results]
        )


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestCreateUser:
    async def test_unauthorized(
        self,
        unauthorized_api_assertions: HTTPXResponseAssertion,
        test_client_api: httpx.AsyncClient,
    ):
        response = await test_client_api.post("/users/", json={})

        unauthorized_api_assertions(response)

    @pytest.mark.authenticated_admin
    async def test_invalid_json_payload(self, test_client_api: httpx.AsyncClient):
        response = await test_client_api.post("/users/", content='{"foo": "bar",}')

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.authenticated_admin
    async def test_unknown_tenant(
        self, test_client_api: httpx.AsyncClient, not_existing_uuid: uuid.UUID
    ):
        response = await test_client_api.post(
            "/users/",
            json={
                "email": "louis@bretagne.duchy",
                "email_verified": True,
                "password": "herminetincture",
                "fields": {},
                "tenant_id": str(not_existing_uuid),
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        json = response.json()
        assert json["detail"] == APIErrorCode.USER_CREATE_UNKNOWN_TENANT

    @pytest.mark.authenticated_admin
    async def test_existing_user(
        self, test_client_api: httpx.AsyncClient, test_data: TestData
    ):
        tenant = test_data["tenants"]["default"]
        response = await test_client_api.post(
            "/users/",
            json={
                "email": "anne@bretagne.duchy",
                "email_verified": True,
                "password": "herminetincture",
                "fields": {},
                "tenant_id": str(tenant.id),
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        json = response.json()
        assert json["detail"] == APIErrorCode.USER_CREATE_ALREADY_EXISTS

    @pytest.mark.parametrize(
        "password",
        [
            pytest.param("h", id="Too short password"),
            pytest.param("h" * 512, id="Too long password"),
        ],
    )
    @pytest.mark.authenticated_admin
    async def test_invalid_password(
        self, password: str, test_client_api: httpx.AsyncClient, test_data: TestData
    ):
        tenant = test_data["tenants"]["default"]
        response = await test_client_api.post(
            "/users/",
            json={
                "email": "louis@bretagne.duchy",
                "email_verified": True,
                "password": password,
                "fields": {},
                "tenant_id": str(tenant.id),
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        json = response.json()
        assert json["detail"] == APIErrorCode.USER_CREATE_INVALID_PASSWORD
        assert "reason" in json

    @pytest.mark.authenticated_admin
    async def test_invalid_field_value(
        self, test_client_api: httpx.AsyncClient, test_data: TestData
    ):
        tenant = test_data["tenants"]["default"]
        response = await test_client_api.post(
            "/users/",
            json={
                "email": "louis@bretagne.duchy",
                "email_verified": True,
                "password": "herminetincture",
                "fields": {
                    "last_seen": "INVALID_VALUE",
                },
                "tenant_id": str(tenant.id),
            },
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        json = response.json()
        assert json["detail"][0]["loc"] == ["body", "fields", "last_seen"]

    @pytest.mark.authenticated_admin
    async def test_valid(
        self,
        test_client_api: httpx.AsyncClient,
        test_data: TestData,
        send_task_mock: MagicMock,
        workspace: Workspace,
    ):
        tenant = test_data["tenants"]["default"]
        response = await test_client_api.post(
            "/users/",
            json={
                "email": "louis@bretagne.duchy",
                "email_verified": True,
                "password": "herminetincture",
                "fields": {
                    "onboarding_done": True,
                    "last_seen": "2022-01-01T13:37:00+00:00",
                },
                "tenant_id": str(tenant.id),
            },
        )

        assert response.status_code == status.HTTP_201_CREATED

        json = response.json()
        assert json["email"] == "louis@bretagne.duchy"
        assert json["tenant_id"] == str(tenant.id)
        assert json["tenant"]["id"] == str(tenant.id)

        assert json["fields"]["onboarding_done"] is True
        assert json["fields"]["last_seen"] == "2022-01-01T13:37:00Z"

        send_task_mock.assert_called_with(
            on_after_register, json["id"], str(workspace.id)
        )


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestUpdateUser:
    async def test_unauthorized(
        self,
        unauthorized_api_assertions: HTTPXResponseAssertion,
        test_client_api: httpx.AsyncClient,
        test_data: TestData,
    ):
        user = test_data["users"]["regular"]
        response = await test_client_api.patch(f"/users/{user.id}", json={})

        unauthorized_api_assertions(response)

    @pytest.mark.authenticated_admin
    async def test_unknown_user(
        self, test_client_api: httpx.AsyncClient, not_existing_uuid: uuid.UUID
    ):
        response = await test_client_api.patch(f"/users/{not_existing_uuid}", json={})

        print(response.json())
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.authenticated_admin
    async def test_invalid_json_payload(
        self, test_client_api: httpx.AsyncClient, test_data: TestData
    ):
        user = test_data["users"]["regular"]
        response = await test_client_api.patch(
            f"/users/{user.id}", content='{"foo": "bar",}'
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.authenticated_admin
    async def test_existing_email_address(
        self, test_client_api: httpx.AsyncClient, test_data: TestData
    ):
        user = test_data["users"]["regular"]
        response = await test_client_api.patch(
            f"/users/{user.id}",
            json={"email": "isabeau@bretagne.duchy"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        json = response.json()
        assert json["detail"] == APIErrorCode.USER_UPDATE_EMAIL_ALREADY_EXISTS

    @pytest.mark.authenticated_admin
    async def test_invalid_password(
        self, test_client_api: httpx.AsyncClient, test_data: TestData
    ):
        user = test_data["users"]["regular"]
        response = await test_client_api.patch(
            f"/users/{user.id}",
            json={"password": "h"},
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        json = response.json()
        assert json["detail"] == APIErrorCode.USER_UPDATE_INVALID_PASSWORD
        assert "reason" in json

    @pytest.mark.authenticated_admin
    async def test_invalid_field_value(
        self, test_client_api: httpx.AsyncClient, test_data: TestData
    ):
        user = test_data["users"]["regular"]
        response = await test_client_api.patch(
            f"/users/{user.id}", json={"fields": {"last_seen": "INVALID_VALUE"}}
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        json = response.json()
        assert json["detail"][0]["loc"] == ["body", "fields", "last_seen"]

    @pytest.mark.authenticated_admin
    async def test_valid(self, test_client_api: httpx.AsyncClient, test_data: TestData):
        user = test_data["users"]["regular"]
        response = await test_client_api.patch(
            f"/users/{user.id}",
            json={
                "email": "anne+updated@bretagne.duchy",
                "password": "herminetincture",
                "fields": {
                    "onboarding_done": True,
                    "last_seen": "2022-01-01T13:37:00+00:00",
                },
            },
        )

        assert response.status_code == status.HTTP_200_OK

        json = response.json()
        assert json["email"] == "anne+updated@bretagne.duchy"

        assert json["fields"]["onboarding_done"] is True
        assert json["fields"]["last_seen"] == "2022-01-01T13:37:00Z"

        assert json["tenant"]["id"] == str(user.tenant_id)


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestDeleteUser:
    async def test_unauthorized(
        self,
        unauthorized_api_assertions: HTTPXResponseAssertion,
        test_client_api: httpx.AsyncClient,
        test_data: TestData,
    ):
        user = test_data["users"]["regular"]
        response = await test_client_api.delete(f"/users/{user.id}")

        unauthorized_api_assertions(response)

    @pytest.mark.authenticated_admin
    async def test_not_existing(
        self, test_client_api: httpx.AsyncClient, not_existing_uuid: uuid.UUID
    ):
        response = await test_client_api.delete(f"/users/{not_existing_uuid}")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.authenticated_admin
    async def test_valid(self, test_client_api: httpx.AsyncClient, test_data: TestData):
        user = test_data["users"]["regular"]
        response = await test_client_api.delete(f"/users/{user.id}")

        assert response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestCreateUserAccessToken:
    async def test_unauthorized(
        self, test_client_api: httpx.AsyncClient, test_data: TestData
    ):
        user = test_data["users"]["regular"]
        response = await test_client_api.post(f"/users/{user.id}/access-token", json={})

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.authenticated_admin
    async def test_unknown_user(
        self, test_client_api: httpx.AsyncClient, not_existing_uuid: uuid.UUID
    ):
        response = await test_client_api.post(
            f"/users/{not_existing_uuid}/access-token", json={}
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.authenticated_admin
    async def test_unknown_client(
        self,
        test_client_api: httpx.AsyncClient,
        test_data: TestData,
        not_existing_uuid: uuid.UUID,
    ):
        user = test_data["users"]["regular"]
        response = await test_client_api.post(
            f"/users/{user.id}/access-token",
            json={
                "client_id": str(not_existing_uuid),
                "scopes": ["openid"],
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        json = response.json()
        assert json["detail"] == APIErrorCode.USER_CREATE_ACCESS_TOKEN_UNKNOWN_CLIENT

    @pytest.mark.authenticated_admin
    async def test_client_not_in_user_tenant(
        self, test_client_api: httpx.AsyncClient, test_data: TestData
    ):
        user = test_data["users"]["regular"]
        response = await test_client_api.post(
            f"/users/{user.id}/access-token",
            json={
                "client_id": str(test_data["clients"]["secondary_tenant"].id),
                "scopes": ["openid"],
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        json = response.json()
        assert json["detail"] == APIErrorCode.USER_CREATE_ACCESS_TOKEN_UNKNOWN_CLIENT

    @pytest.mark.authenticated_admin
    async def test_valid(self, test_client_api: httpx.AsyncClient, test_data: TestData):
        user = test_data["users"]["regular"]
        response = await test_client_api.post(
            f"/users/{str(user.id)}/access-token",
            json={
                "client_id": str(test_data["clients"]["default_tenant"].id),
                "scopes": ["openid"],
            },
        )

        assert response.status_code == status.HTTP_200_OK

        json = response.json()
        assert "access_token" in json
        assert json["token_type"] == "bearer"
        assert "expires_in" in json


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestListUserPermissions:
    async def test_unauthorized(
        self,
        unauthorized_api_assertions: HTTPXResponseAssertion,
        test_client_api: httpx.AsyncClient,
        test_data: TestData,
    ):
        user = test_data["users"]["regular"]
        response = await test_client_api.get(f"/users/{user.id}/permissions")

        unauthorized_api_assertions(response)

    @pytest.mark.authenticated_admin
    async def test_unknown_user(
        self, test_client_api: httpx.AsyncClient, not_existing_uuid: uuid.UUID
    ):
        response = await test_client_api.get(f"/users/{not_existing_uuid}/permissions")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.authenticated_admin
    async def test_valid(self, test_client_api: httpx.AsyncClient, test_data: TestData):
        user = test_data["users"]["regular"]
        response = await test_client_api.get(f"/users/{user.id}/permissions")

        assert response.status_code == status.HTTP_200_OK

        json = response.json()

        assert json["count"] == 2
        assert len(json["results"]) == 2

        for result in json["results"]:
            assert "id" not in result
            assert result["user_id"] == str(user.id)
            assert "permission" in result
            assert result["permission_id"] == result["permission"]["id"]
            assert "from_role" in result
            if result["from_role_id"] is not None:
                assert result["from_role_id"] == result["from_role"]["id"]


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestCreateUserPermission:
    async def test_unauthorized(
        self,
        unauthorized_api_assertions: HTTPXResponseAssertion,
        test_client_api: httpx.AsyncClient,
        test_data: TestData,
    ):
        user = test_data["users"]["regular"]
        permission = test_data["permissions"]["castles:delete"]
        response = await test_client_api.post(
            f"/users/{user.id}/permissions", json={"id": str(permission.id)}
        )

        unauthorized_api_assertions(response)

    @pytest.mark.authenticated_admin
    async def test_unknown_user(
        self,
        test_client_api: httpx.AsyncClient,
        not_existing_uuid: uuid.UUID,
        test_data: TestData,
    ):
        permission = test_data["permissions"]["castles:create"]
        response = await test_client_api.post(
            f"/users/{not_existing_uuid}/permissions", json={"id": str(permission.id)}
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.authenticated_admin
    async def test_unknown_role(
        self,
        test_client_api: httpx.AsyncClient,
        not_existing_uuid: uuid.UUID,
        test_data: TestData,
    ):
        user = test_data["users"]["regular"]
        response = await test_client_api.post(
            f"/users/{user.id}/permissions", json={"id": str(not_existing_uuid)}
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        json = response.json()
        assert (
            json["detail"]
            == APIErrorCode.USER_PERMISSION_CREATE_NOT_EXISTING_PERMISSION
        )

    @pytest.mark.authenticated_admin
    async def test_already_added_permission(
        self, test_client_api: httpx.AsyncClient, test_data: TestData
    ):
        permission = test_data["permissions"]["castles:delete"]
        user = test_data["users"]["regular"]
        response = await test_client_api.post(
            f"/users/{user.id}/permissions", json={"id": str(permission.id)}
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        json = response.json()
        assert (
            json["detail"]
            == APIErrorCode.USER_PERMISSION_CREATE_ALREADY_ADDED_PERMISSION
        )

    @pytest.mark.parametrize("permission_alias", ["castles:create", "castles:read"])
    @pytest.mark.authenticated_admin
    async def test_valid(
        self,
        permission_alias: str,
        test_client_api: httpx.AsyncClient,
        test_data: TestData,
        workspace_session: AsyncSession,
    ):
        permission = test_data["permissions"][permission_alias]
        user = test_data["users"]["regular"]
        response = await test_client_api.post(
            f"/users/{user.id}/permissions", json={"id": str(permission.id)}
        )

        assert response.status_code == status.HTTP_201_CREATED

        user_permission_repository = UserPermissionRepository(workspace_session)
        user_permissions = await user_permission_repository.list(
            user_permission_repository.get_by_user_statement(user.id, direct_only=True)
        )
        assert len(user_permissions) == 2
        assert permission.id in [
            user_permission.permission_id for user_permission in user_permissions
        ]


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestDeleteUserPermission:
    async def test_unauthorized(
        self,
        unauthorized_api_assertions: HTTPXResponseAssertion,
        test_client_api: httpx.AsyncClient,
        test_data: TestData,
    ):
        user = test_data["users"]["regular"]
        permission = test_data["permissions"]["castles:delete"]
        response = await test_client_api.delete(
            f"/users/{user.id}/permissions/{permission.id}"
        )

        unauthorized_api_assertions(response)

    @pytest.mark.authenticated_admin
    async def test_unknown_user(
        self,
        test_client_api: httpx.AsyncClient,
        not_existing_uuid: uuid.UUID,
        test_data: TestData,
    ):
        permission = test_data["permissions"]["castles:delete"]
        response = await test_client_api.delete(
            f"/users/{not_existing_uuid}/permissions/{permission.id}"
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.authenticated_admin
    async def test_not_added_permission(
        self, test_client_api: httpx.AsyncClient, test_data: TestData
    ):
        user = test_data["users"]["regular"]
        permission = test_data["permissions"]["castles:create"]
        response = await test_client_api.delete(
            f"/users/{user.id}/permissions/{permission.id}"
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.authenticated_admin
    async def test_valid(
        self,
        test_client_api: httpx.AsyncClient,
        test_data: TestData,
        workspace_session: AsyncSession,
    ):
        permission = test_data["permissions"]["castles:delete"]
        user = test_data["users"]["regular"]
        response = await test_client_api.delete(
            f"/users/{user.id}/permissions/{permission.id}"
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT

        user_permission_repository = UserPermissionRepository(workspace_session)
        user_permissions = await user_permission_repository.list(
            user_permission_repository.get_by_user_statement(user.id, direct_only=True)
        )
        assert len(user_permissions) == 0


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestListUserRoles:
    async def test_unauthorized(
        self,
        unauthorized_api_assertions: HTTPXResponseAssertion,
        test_client_api: httpx.AsyncClient,
        test_data: TestData,
    ):
        user = test_data["users"]["regular"]
        response = await test_client_api.get(f"/users/{user.id}/roles")

        unauthorized_api_assertions(response)

    @pytest.mark.authenticated_admin
    async def test_unknown_user(
        self, test_client_api: httpx.AsyncClient, not_existing_uuid: uuid.UUID
    ):
        response = await test_client_api.get(f"/users/{not_existing_uuid}/roles")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.authenticated_admin
    async def test_valid(self, test_client_api: httpx.AsyncClient, test_data: TestData):
        user = test_data["users"]["regular"]
        response = await test_client_api.get(f"/users/{user.id}/roles")

        assert response.status_code == status.HTTP_200_OK

        json = response.json()

        assert json["count"] == 1
        assert len(json["results"]) == 1

        for result in json["results"]:
            assert "id" not in result
            assert result["user_id"] == str(user.id)
            assert "role" in result
            assert result["role_id"] == result["role"]["id"]


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestCreateUserRole:
    async def test_unauthorized(
        self,
        unauthorized_api_assertions: HTTPXResponseAssertion,
        test_client_api: httpx.AsyncClient,
        test_data: TestData,
    ):
        user = test_data["users"]["regular"]
        role = test_data["roles"]["castles_manager"]
        response = await test_client_api.post(
            f"/users/{user.id}/roles", json={"id": str(role.id)}
        )

        unauthorized_api_assertions(response)

    @pytest.mark.authenticated_admin
    async def test_unknown_user(
        self,
        test_client_api: httpx.AsyncClient,
        not_existing_uuid: uuid.UUID,
        test_data: TestData,
    ):
        role = test_data["roles"]["castles_manager"]
        response = await test_client_api.post(
            f"/users/{not_existing_uuid}/roles", json={"id": str(role.id)}
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.authenticated_admin
    async def test_unknown_role(
        self,
        test_client_api: httpx.AsyncClient,
        not_existing_uuid: uuid.UUID,
        test_data: TestData,
    ):
        user = test_data["users"]["regular"]
        response = await test_client_api.post(
            f"/users/{user.id}/roles", json={"id": str(not_existing_uuid)}
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        json = response.json()
        assert json["detail"] == APIErrorCode.USER_ROLE_CREATE_NOT_EXISTING_ROLE

    @pytest.mark.authenticated_admin
    async def test_already_added_role(
        self, test_client_api: httpx.AsyncClient, test_data: TestData
    ):
        role = test_data["roles"]["castles_visitor"]
        user = test_data["users"]["regular"]
        response = await test_client_api.post(
            f"/users/{user.id}/roles", json={"id": str(role.id)}
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        json = response.json()
        assert json["detail"] == APIErrorCode.USER_ROLE_CREATE_ALREADY_ADDED_ROLE

    @pytest.mark.authenticated_admin
    async def test_valid(
        self,
        test_client_api: httpx.AsyncClient,
        test_data: TestData,
        workspace: Workspace,
        workspace_session: AsyncSession,
        send_task_mock: MagicMock,
    ):
        role = test_data["roles"]["castles_manager"]
        user = test_data["users"]["regular"]
        response = await test_client_api.post(
            f"/users/{user.id}/roles", json={"id": str(role.id)}
        )

        assert response.status_code == status.HTTP_201_CREATED

        user_role_repository = UserRoleRepository(workspace_session)
        user_roles = await user_role_repository.list(
            user_role_repository.get_by_user_statement(user.id)
        )
        assert len(user_roles) == 2
        assert role.id in [user_role.role_id for user_role in user_roles]

        send_task_mock.assert_called_with(
            on_user_role_created, str(user.id), str(role.id), str(workspace.id)
        )


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestDeleteUserRole:
    async def test_unauthorized(
        self,
        unauthorized_api_assertions: HTTPXResponseAssertion,
        test_client_api: httpx.AsyncClient,
        test_data: TestData,
    ):
        user = test_data["users"]["regular"]
        role = test_data["roles"]["castles_visitor"]
        response = await test_client_api.delete(f"/users/{user.id}/roles/{role.id}")

        unauthorized_api_assertions(response)

    @pytest.mark.authenticated_admin
    async def test_unknown_user(
        self,
        test_client_api: httpx.AsyncClient,
        not_existing_uuid: uuid.UUID,
        test_data: TestData,
    ):
        role = test_data["roles"]["castles_visitor"]
        response = await test_client_api.delete(
            f"/users/{not_existing_uuid}/roles/{role.id}"
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.authenticated_admin
    async def test_not_added_role(
        self, test_client_api: httpx.AsyncClient, test_data: TestData
    ):
        user = test_data["users"]["regular"]
        role = test_data["roles"]["castles_manager"]
        response = await test_client_api.delete(f"/users/{user.id}/roles/{role.id}")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.authenticated_admin
    async def test_valid(
        self,
        test_client_api: httpx.AsyncClient,
        test_data: TestData,
        workspace: Workspace,
        workspace_session: AsyncSession,
        send_task_mock: MagicMock,
    ):
        role = test_data["roles"]["castles_visitor"]
        user = test_data["users"]["regular"]
        response = await test_client_api.delete(f"/users/{user.id}/roles/{role.id}")

        assert response.status_code == status.HTTP_204_NO_CONTENT

        user_role_repository = UserRoleRepository(workspace_session)
        user_roles = await user_role_repository.list(
            user_role_repository.get_by_user_statement(user.id)
        )
        assert len(user_roles) == 0

        send_task_mock.assert_called_with(
            on_user_role_deleted, str(user.id), str(role.id), str(workspace.id)
        )


@pytest.mark.asyncio
@pytest.mark.workspace_host
class TestListUserOAuthAccounts:
    async def test_unauthorized(
        self,
        unauthorized_api_assertions: HTTPXResponseAssertion,
        test_client_api: httpx.AsyncClient,
        test_data: TestData,
    ):
        user = test_data["users"]["regular"]
        response = await test_client_api.get(f"/users/{user.id}/oauth-accounts")

        unauthorized_api_assertions(response)

    @pytest.mark.authenticated_admin
    async def test_unknown_user(
        self, test_client_api: httpx.AsyncClient, not_existing_uuid: uuid.UUID
    ):
        response = await test_client_api.get(
            f"/users/{not_existing_uuid}/oauth-accounts"
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.authenticated_admin
    async def test_valid(self, test_client_api: httpx.AsyncClient, test_data: TestData):
        user = test_data["users"]["regular"]
        response = await test_client_api.get(f"/users/{user.id}/oauth-accounts")

        assert response.status_code == status.HTTP_200_OK

        json = response.json()

        assert json["count"] == 2
        assert len(json["results"]) == 2

        for result in json["results"]:
            assert "id" in result
            assert "access_token" not in result
            assert "refresh_token" not in result
            assert "expires_at" not in result
            assert "oauth_provider" in result
