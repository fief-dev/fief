import pytest
from starlette.datastructures import FormData
from wtforms import Form

from fief.apps.auth.forms.register import (
    AddressFormField,
    CountryField,
    PhoneNumberField,
    RegisterFormBase,
    UserFieldType,
    get_register_form_class,
)
from fief.models import UserField


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
        print(form.errors)
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


@pytest.mark.asyncio
class TestGetRegisterFormClass:
    async def test_basic(self):
        user_fields: list[UserField] = [
            UserField(
                name="First name",
                slug="first_name",
                type=UserFieldType.STRING,
                configuration={
                    "at_registration": True,
                    "required": True,
                    "at_update": True,
                    "default": None,
                    "choices": None,
                },
            ),
        ]
        form_class = await get_register_form_class(user_fields, None)
        assert issubclass(form_class, RegisterFormBase)

        form = form_class(
            FormData(
                {
                    "email": "anne@bretagne.duchy",
                    "password": "hermine",
                    "fields.first_name": "Anne",
                }
            ),
            meta={"csrf": False},
        )

        assert form.validate() is True
        assert form.fields.first_name.data == "Anne"

    async def test_missing_required_field(self):
        user_fields: list[UserField] = [
            UserField(
                name="First name",
                slug="first_name",
                type=UserFieldType.STRING,
                configuration={
                    "at_registration": True,
                    "required": True,
                    "at_update": True,
                    "default": None,
                    "choices": None,
                },
            ),
        ]
        form_class = await get_register_form_class(user_fields, None)
        assert issubclass(form_class, RegisterFormBase)

        form = form_class(
            FormData({"email": "anne@bretagne.duchy", "password": "hermine"}),
            meta={"csrf": False},
        )

        assert form.validate() is False
        assert len(form.errors) == 1
        assert form.fields.first_name.errors == ["This field is required."]

    async def test_invalid_empty_string(self):
        user_fields: list[UserField] = [
            UserField(
                name="First name",
                slug="first_name",
                type=UserFieldType.STRING,
                configuration={
                    "at_registration": True,
                    "required": True,
                    "at_update": True,
                    "default": None,
                    "choices": None,
                },
            ),
        ]
        form_class = await get_register_form_class(user_fields, None)
        assert issubclass(form_class, RegisterFormBase)

        form = form_class(
            FormData(
                {
                    "email": "anne@bretagne.duchy",
                    "password": "hermine",
                    "fields.first_name": "",
                }
            ),
            meta={"csrf": False},
        )

        assert form.validate() is False
        assert len(form.errors) == 1
        assert form.fields.first_name.errors == ["This field is required."]

    async def test_missing_boolean_field(self):
        user_fields: list[UserField] = [
            UserField(
                name="Subscribe to newsletter",
                slug="newsletter",
                type=UserFieldType.BOOLEAN,
                configuration={
                    "at_registration": True,
                    "required": False,
                    "at_update": True,
                    "default": None,
                    "choices": None,
                },
            ),
        ]
        form_class = await get_register_form_class(user_fields, None)
        assert issubclass(form_class, RegisterFormBase)

        form = form_class(
            FormData({"email": "anne@bretagne.duchy", "password": "hermine"}),
            meta={"csrf": False},
        )

        assert form.validate() is True
        assert form.fields.newsletter.data is False

    async def test_provided_boolean_field(self):
        user_fields: list[UserField] = [
            UserField(
                name="Subscribe to newsletter",
                slug="newsletter",
                type=UserFieldType.BOOLEAN,
                configuration={
                    "at_registration": True,
                    "required": False,
                    "at_update": True,
                    "default": None,
                    "choices": None,
                },
            ),
        ]
        form_class = await get_register_form_class(user_fields, None)
        assert issubclass(form_class, RegisterFormBase)

        form = form_class(
            FormData(
                {
                    "email": "anne@bretagne.duchy",
                    "password": "hermine",
                    "fields.newsletter": "on",
                }
            ),
            meta={"csrf": False},
        )

        assert form.validate() is True
        assert form.fields.newsletter.data is True

    @pytest.mark.parametrize("value", [None, ""])
    async def test_required_boolean_field_false(self, value: str | None):
        user_fields: list[UserField] = [
            UserField(
                name="Consent",
                slug="consent",
                type=UserFieldType.BOOLEAN,
                configuration={
                    "at_registration": True,
                    "required": True,
                    "at_update": True,
                    "default": None,
                    "choices": None,
                },
            ),
        ]
        form_class = await get_register_form_class(user_fields, None)
        assert issubclass(form_class, RegisterFormBase)

        data = {"email": "anne@bretagne.duchy", "password": "hermine"}
        if value is not None:
            data["fields.consent"] = value
        form = form_class(FormData(data), meta={"csrf": False})

        assert form.validate() is False
        assert len(form.errors) == 1
        assert form.fields.consent.errors == ["This field is required."]

    async def test_required_boolean_field_true(self):
        user_fields: list[UserField] = [
            UserField(
                name="Consent",
                slug="consent",
                type=UserFieldType.BOOLEAN,
                configuration={
                    "at_registration": True,
                    "required": True,
                    "at_update": True,
                    "default": None,
                    "choices": None,
                },
            ),
        ]
        form_class = await get_register_form_class(user_fields, None)
        assert issubclass(form_class, RegisterFormBase)

        form = form_class(
            FormData(
                {
                    "email": "anne@bretagne.duchy",
                    "password": "hermine",
                    "fields.consent": "on",
                }
            ),
            meta={"csrf": False},
        )

        assert form.validate() is True
        assert form.fields.consent.data is True

    async def test_invalid_choice(self):
        user_fields: list[UserField] = [
            UserField(
                name="Choice",
                slug="choice",
                type=UserFieldType.CHOICE,
                configuration={
                    "at_registration": True,
                    "required": True,
                    "at_update": True,
                    "default": None,
                    "choices": [("a", "A"), ("b", "B"), ("c", "C")],
                },
            ),
        ]
        form_class = await get_register_form_class(user_fields, None)
        assert issubclass(form_class, RegisterFormBase)

        form = form_class(
            FormData(
                {
                    "email": "anne@bretagne.duchy",
                    "password": "hermine",
                    "fields.choice": "d",
                }
            ),
            meta={"csrf": False},
        )

        assert form.validate() is False
        assert len(form.errors) == 1
        assert form.fields.choice.errors == ["Not a valid choice."]

    async def test_valid_choice(self):
        user_fields: list[UserField] = [
            UserField(
                name="Choice",
                slug="choice",
                type=UserFieldType.CHOICE,
                configuration={
                    "at_registration": True,
                    "required": True,
                    "at_update": True,
                    "default": None,
                    "choices": [("a", "A"), ("b", "B"), ("c", "C")],
                },
            ),
        ]
        form_class = await get_register_form_class(user_fields, None)
        assert issubclass(form_class, RegisterFormBase)

        form = form_class(
            FormData(
                {
                    "email": "anne@bretagne.duchy",
                    "password": "hermine",
                    "fields.choice": "a",
                }
            ),
            meta={"csrf": False},
        )

        assert form.validate() is True
        assert form.fields.choice.data == "a"

    async def test_phone_number(self):
        user_fields: list[UserField] = [
            UserField(
                name="Phone number",
                slug="phone_number",
                type=UserFieldType.PHONE_NUMBER,
                configuration={
                    "at_registration": True,
                    "required": True,
                    "at_update": True,
                    "default": None,
                    "choices": None,
                },
            ),
        ]
        form_class = await get_register_form_class(user_fields, None)
        assert issubclass(form_class, RegisterFormBase)

        form = form_class(
            FormData(
                {
                    "email": "anne@bretagne.duchy",
                    "password": "hermine",
                    "fields.phone_number": "+33102030405",
                }
            ),
            meta={"csrf": False},
        )

        assert form.validate() is True
        assert form.fields.phone_number.data == "+33102030405"

    async def test_optional_address(self):
        user_fields: list[UserField] = [
            UserField(
                name="Address",
                slug="address",
                type=UserFieldType.ADDRESS,
                configuration={
                    "at_registration": True,
                    "required": False,
                    "at_update": True,
                    "default": None,
                    "choices": None,
                },
            ),
        ]
        form_class = await get_register_form_class(user_fields, None)
        assert issubclass(form_class, RegisterFormBase)

        form = form_class(
            FormData({"email": "anne@bretagne.duchy", "password": "hermine"}),
            meta={"csrf": False},
        )

        assert form.validate() is True
        assert form.fields.address.data is None
