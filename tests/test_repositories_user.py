import pytest

from fief.db import AsyncSession
from fief.repositories import UserRepository
from tests.data import TestData


@pytest.mark.parametrize(
    "email,tenant_alias,user_alias",
    [
        ("anne@bretagne.duchy", "default", "regular"),
        ("ANNE@bretagne.DUCHY", "default", "regular"),
        ("ANNE@nantes.city", "default", None),
        ("anne@nantes.city", "secondary", "regular_secondary"),
        ("Claude@bretagne.duchy", "default", "cased_email"),
        ("claude@bretagne.duchy", "default", "cased_email"),
    ],
)
@pytest.mark.asyncio
async def test_get_by_email_and_tenant(
    email: str,
    tenant_alias: str,
    user_alias: str | None,
    workspace_session: AsyncSession,
    test_data: TestData,
):
    tenant = test_data["tenants"][tenant_alias]

    user_repository = UserRepository(workspace_session)

    user = await user_repository.get_by_email_and_tenant(email, tenant.id)

    if user_alias is None:
        assert user is None
    else:
        assert user is not None
        assert user.id == test_data["users"][user_alias].id
