import pytest
from starlette.datastructures import FormData
from wtforms import Form

from fief.forms import AddressFormField, CountryField, PhoneNumberField, TimezoneField


class TestPhoneNumberField:
    class PhoneNumberForm(Form):
        phone_number = PhoneNumberField()

    @pytest.mark.parametrize("phone_number", ["123", "0102030405", "+33123"])
    def test_invalid(self, phone_number: str):
        form = TestPhoneNumberField.PhoneNumberForm(
            FormData({"phone_number": phone_number})
        )
        assert form.validate() is False
        assert len(form.phone_number.errors) == 1

        form = TestPhoneNumberField.PhoneNumberForm(data={"phone_number": phone_number})
        assert form.validate() is False
        assert len(form.phone_number.errors) == 1

    @pytest.mark.parametrize(
        "phone_number,formatted",
        [
            ("+33102030405", "+33102030405"),
            ("+33 1 02 03 04 05", "+33102030405"),
        ],
    )
    def test_valid(self, phone_number: str, formatted: str):
        form = TestPhoneNumberField.PhoneNumberForm(
            FormData({"phone_number": phone_number})
        )
        assert form.validate() is True
        assert form.phone_number.data == formatted

        form = TestPhoneNumberField.PhoneNumberForm(data={"phone_number": phone_number})
        assert form.validate() is True
        assert form.phone_number.data == formatted


class TestCountryField:
    class CountryForm(Form):
        country = CountryField()

    @pytest.mark.parametrize("country", ["XX", "ZZ"])
    def test_invalid(self, country: str):
        form = TestCountryField.CountryForm(FormData({"country": country}))
        assert form.validate() is False
        assert len(form.country.errors) == 1

    @pytest.mark.parametrize("country", ["FR", "US", "DE"])
    def test_valid(self, country: str):
        form = TestCountryField.CountryForm(FormData({"country": country}))
        assert form.validate() is True
        assert form.country.data == country


class TestAddressFormField:
    class AddressForm(Form):
        address = AddressFormField()

    @pytest.mark.parametrize(
        "data,nb_errors",
        [
            ({}, 4),
            ({"address.line1": "4 place Marc Elder"}, 3),
            (
                {
                    "address.line1": "4 place Marc Elder",
                    "address.postal_code": "44000",
                    "address.city": "Nantes",
                    "address.country": "FRANCE",
                },
                1,
            ),
            (
                {
                    "address.line1": "",
                    "address.postal_code": "",
                    "address.city": "",
                    "address.country": "",
                },
                4,
            ),
        ],
    )
    def test_invalid(self, data: dict[str, str], nb_errors: int):
        form = TestAddressFormField.AddressForm(FormData(data))
        assert form.validate() is False
        assert len(form.address.errors) == nb_errors

    def test_valid(self):
        form = TestAddressFormField.AddressForm(
            FormData(
                {
                    "address.line1": "4 place Marc Elder",
                    "address.postal_code": "44000",
                    "address.city": "Nantes",
                    "address.country": "FR",
                }
            )
        )
        assert form.validate() is True

        assert form.address.line1.data == "4 place Marc Elder"
        assert form.address.line2.data is None
        assert form.address.postal_code.data == "44000"
        assert form.address.city.data == "Nantes"
        assert form.address.state.data is None
        assert form.address.country.data == "FR"


class TestTimezoneField:
    class TimezoneForm(Form):
        timezone = TimezoneField()

    @pytest.mark.parametrize("timezone", ["Europe/Nantes", "US/Paris"])
    def test_invalid(self, timezone: str):
        form = TestTimezoneField.TimezoneForm(FormData({"timezone": timezone}))
        assert form.validate() is False
        assert len(form.timezone.errors) == 1

    @pytest.mark.parametrize("timezone", ["Europe/Paris", "US/Eastern"])
    def test_valid(self, timezone: str):
        form = TestTimezoneField.TimezoneForm(FormData({"timezone": timezone}))
        assert form.validate() is True
        assert form.timezone.data == timezone
