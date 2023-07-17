from datetime import UTC, date, datetime

import pytest

from tests.data import TestData


@pytest.mark.asyncio
async def test_fields(test_data: TestData):
    user = test_data["users"]["regular"]
    assert user.fields == {
        "gender": "F",
        "given_name": "Anne",
        "phone_number": "+33642424242",
        "phone_number_verified": True,
        "birthdate": date(1477, 1, 25),
        "last_seen": datetime(2022, 1, 1, 0, 0, 0, tzinfo=UTC),
        "address": {
            "line1": "4 place Marc Elder",
            "postal_code": "44000",
            "city": "Nantes",
            "country": "FR",
        },
        "onboarding_done": False,
    }


@pytest.mark.asyncio
async def test_get_claims(test_data: TestData):
    user = test_data["users"]["regular"]
    assert user.get_claims() == {
        "sub": str(user.id),
        "email": user.email,
        "email_verified": user.email_verified,
        "is_active": True,
        "tenant_id": str(user.tenant_id),
        "fields": {
            "gender": "F",
            "given_name": "Anne",
            "phone_number": "+33642424242",
            "phone_number_verified": True,
            "birthdate": "1477-01-25",
            "last_seen": "2022-01-01T00:00:00+00:00",
            "address": {
                "line1": "4 place Marc Elder",
                "postal_code": "44000",
                "city": "Nantes",
                "country": "FR",
            },
            "onboarding_done": False,
        },
    }
