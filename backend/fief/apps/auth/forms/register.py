import functools
from typing import List, Mapping, Optional, Type, TypeVar

import phonenumbers
import pycountry
import pytz
from fastapi import Depends
from wtforms import (
    BooleanField,
    DateField,
    DateTimeLocalField,
    EmailField,
    Field,
    FormField,
    IntegerField,
    PasswordField,
    SelectField,
    StringField,
    TelField,
    validators,
)
from wtforms.utils import unset_value

from fief.apps.auth.forms.base import BaseForm, CSRFBaseForm
from fief.dependencies.user_field import get_registration_user_fields
from fief.locale import gettext_lazy as _
from fief.models import UserField, UserFieldType


def empty_string_to_none(value: Optional[str]) -> Optional[str]:
    if value is None or value == "":
        return None
    return value


class PhoneNumberField(TelField):
    def process_data(self, value):
        if value is None or value is unset_value:
            self.data = None
            return

        self.data = self._validate_phone_number(value)

    def process_formdata(self, valuelist):
        if not valuelist:
            return

        self.data = self._validate_phone_number(valuelist[0])

    def _validate_phone_number(self, value: str) -> str:
        try:
            parsed = phonenumbers.parse(value)
        except phonenumbers.phonenumberutil.NumberParseException as e:
            raise ValueError(_("The country code is missing.")) from e
        if not phonenumbers.is_valid_number(parsed):
            raise ValueError(_("This phone number is invalid."))
        return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)


class CountryField(SelectField):
    def __init__(self, *args, **kwargs):
        countries = sorted(pycountry.countries, key=lambda c: c.name)
        choices = [(country.alpha_2, country.name) for country in countries]
        super().__init__(*args, choices=choices, **kwargs)


class AddressForm(BaseForm):
    def __init__(self, *args, required: bool = True, **kwargs):
        self.required = required
        super().__init__(*args, **kwargs)

    line1 = StringField(_("Address line 1"), validators=[validators.InputRequired()])
    line2 = StringField(
        _("Address line 2"),
        validators=[validators.Optional()],
        filters=[empty_string_to_none],
    )
    postal_code = StringField(_("Postal code"), validators=[validators.InputRequired()])
    city = StringField(_("City"), validators=[validators.InputRequired()])
    state = StringField(
        _("State"), validators=[validators.Optional()], filters=[empty_string_to_none]
    )
    country = CountryField(_("Country", validators=[validators.InputRequired()]))

    def validate(self, extra_validators=None):
        if self.data is None and not self.required:
            return True
        return super().validate(extra_validators)

    @property
    def data(self):
        data = super().data
        if not any(data.values()):
            return None
        return data


class AddressFormField(FormField):
    def __init__(self, *args, required: bool = True, **kwargs):
        form_class = functools.partial(AddressForm, required=required)
        super().__init__(form_class, separator=".", *args, **kwargs)


class TimezoneField(SelectField):
    def __init__(self, *args, **kwargs):
        choices = sorted(pytz.common_timezones)
        super().__init__(*args, choices=choices, **kwargs)


class RegisterFormBase(CSRFBaseForm):
    email = EmailField(
        _("Email address"), validators=[validators.InputRequired(), validators.Email()]
    )
    password = PasswordField(_("Password"), validators=[validators.InputRequired()])
    fields: FormField


RF = TypeVar("RF", bound=RegisterFormBase)

USER_FIELD_FORM_FIELD_MAP: Mapping[UserFieldType, Field] = {
    UserFieldType.STRING: StringField,
    UserFieldType.INTEGER: IntegerField,
    UserFieldType.BOOLEAN: BooleanField,
    UserFieldType.DATE: DateField,
    UserFieldType.DATETIME: DateTimeLocalField,
    UserFieldType.CHOICE: SelectField,
    UserFieldType.PHONE_NUMBER: PhoneNumberField,
    UserFieldType.ADDRESS: AddressFormField,
    UserFieldType.TIMEZONE: TimezoneField,
}


def _get_form_field(user_field: UserField) -> Field:
    field_validators = []
    required = user_field.get_required()
    if required:
        field_validators.append(validators.InputRequired())
    else:
        field_validators.append(validators.Optional())

    field_kwargs = {
        "label": user_field.name,
        "validators": field_validators,
        "default": user_field.configuration.get("default"),
    }

    if user_field.type == UserFieldType.STRING:
        field_kwargs.update({"filters": [empty_string_to_none]})
    if user_field.type == UserFieldType.CHOICE:
        field_kwargs.update({"choices": user_field.configuration.get("choices")})
    elif user_field.type == UserFieldType.PHONE_NUMBER:
        field_kwargs.update({"render_kw": {"placeholder": "+42102030405"}})
    elif user_field.type == UserFieldType.ADDRESS:
        field_kwargs.update({"required": required})
        field_kwargs.pop("validators")

    return USER_FIELD_FORM_FIELD_MAP[user_field.type](**field_kwargs)


async def get_register_form_class(
    registration_user_fields: List[UserField] = Depends(get_registration_user_fields),
) -> Type[RF]:
    class RegisterFormFields(BaseForm):
        pass

    for field in registration_user_fields:
        setattr(RegisterFormFields, field.slug, _get_form_field(field))

    class RegisterForm(RegisterFormBase):
        fields = FormField(RegisterFormFields, separator=".")

    return RegisterForm
