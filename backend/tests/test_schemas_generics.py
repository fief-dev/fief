from typing import Any

import pytest
from pydantic import BaseModel, ValidationError

from fief.schemas.generics import Address, PhoneNumber, Timezone


class TestPhoneNumber:
    class Model(BaseModel):
        phone_number: PhoneNumber

    @pytest.mark.parametrize("phone_number", ["123", "0102030405", "+33123"])
    def test_invalid(self, phone_number: str):
        with pytest.raises(ValidationError) as e:
            TestPhoneNumber.Model(phone_number=phone_number)

        errors = e.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("phone_number",)

    @pytest.mark.parametrize(
        "phone_number,formatted",
        [
            ("+33102030405", "+33102030405"),
            ("+33 1 02 03 04 05", "+33102030405"),
        ],
    )
    def test_valid(self, phone_number: str, formatted: str):
        o = TestPhoneNumber.Model(phone_number=phone_number)

        assert o.phone_number == formatted


class TestAddress:
    class Model(BaseModel):
        address: Address

    @pytest.mark.parametrize(
        "address,nb_errors",
        [
            ({}, 4),
            ({"line1": "4 place Marc Elder"}, 3),
            (
                {
                    "line1": "4 place Marc Elder",
                    "postal_code": "44000",
                    "city": "Nantes",
                    "country": "FRANCE",
                },
                1,
            ),
            (
                {
                    "line1": "",
                    "postal_code": "",
                    "city": "",
                    "country": "",
                },
                4,
            ),
        ],
    )
    def test_invalid(self, address: dict[str, Any], nb_errors: int):
        with pytest.raises(ValidationError) as e:
            TestAddress.Model(address=address)

        errors = e.value.errors()
        assert len(errors) == nb_errors
        assert errors[0]["loc"][0] == "address"

    def test_valid(self):
        o = TestAddress.Model(
            address={
                "line1": "4 place Marc Elder",
                "postal_code": "44000",
                "city": "Nantes",
                "country": "FR",
            },
        )

        assert o.address.line1 == "4 place Marc Elder"
        assert o.address.line2 is None
        assert o.address.postal_code == "44000"
        assert o.address.city == "Nantes"
        assert o.address.state is None
        assert o.address.country == "FR"


class TestTimezone:
    class Model(BaseModel):
        timezone: Timezone

    @pytest.mark.parametrize("timezone", ["Europe/Nantes", "US/Paris"])
    def test_invalid(self, timezone: str):
        with pytest.raises(ValidationError) as e:
            TestTimezone.Model(timezone=timezone)

        errors = e.value.errors()
        assert len(errors) == 1
        assert errors[0]["loc"] == ("timezone",)

    @pytest.mark.parametrize(
        "timezone,formatted",
        [
            ("Europe/Paris", "Europe/Paris"),
            ("US/Eastern", "US/Eastern"),
            ("EUROPE/PARIS", "Europe/Paris"),
            ("us/eastern", "US/Eastern"),
        ],
    )
    async def test_valid(self, timezone: str, formatted: str):
        o = TestTimezone.Model(timezone=timezone)

        assert o.timezone == formatted
