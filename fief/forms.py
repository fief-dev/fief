import functools
import secrets
from collections.abc import Mapping
from typing import Any, Generic, TypeVar

import phonenumbers
import pycountry
import pytz
from fastapi import Request, status
from starlette.templating import _TemplateResponse
from wtforms import (
    BooleanField,
    DateField,
    DateTimeLocalField,
    Field,
    Form,
    FormField,
    HiddenField,
    IntegerField,
    PasswordField,
    SelectField,
    SelectMultipleField,
    StringField,
    TelField,
    validators,
    widgets,
)
from wtforms.csrf.core import CSRF
from wtforms.utils import unset_value

from fief.locale import get_translations
from fief.locale import gettext_lazy as _
from fief.middlewares.csrf import CSRF_ATTRIBUTE_NAME
from fief.models import UserField, UserFieldType
from fief.services.password import PasswordValidation
from fief.settings import settings
from fief.templates import templates


class CSRFCookieMissingRequest(TypeError):
    def __init__(self) -> None:
        super().__init__("Must provide a Request object for CSRF to work.")


class CSRFCookie(CSRF):
    def setup_form(self, form: Form):
        self.form_meta = form.meta
        return super().setup_form(form)

    def generate_csrf_token(self, csrf_token_field: Field):
        csrf_token: str | None = self.get_challenge_csrf_token()
        if csrf_token is None:
            csrf_token = secrets.token_urlsafe()
            # Will be catched by CSRFCookieSetterMiddleware and set in cookies
            self.request.scope[CSRF_ATTRIBUTE_NAME] = csrf_token

        return csrf_token

    def validate_csrf_token(self, form: Form, field: Field):
        challenge_csrf_token = self.get_challenge_csrf_token()
        if (
            field.data is None
            or challenge_csrf_token is None
            or not secrets.compare_digest(field.data, challenge_csrf_token)
        ):
            raise validators.ValidationError(field.gettext("CSRF failed."))

    def get_challenge_csrf_token(self) -> str | None:
        return self.request.cookies.get(self.form_meta.csrf_cookie_name)

    @property
    def request(self) -> Request:
        try:
            return getattr(self.form_meta, "request")
        except AttributeError as e:
            raise CSRFCookieMissingRequest() from e


class BaseForm(Form):
    class Meta:
        def get_translations(self, form):
            return get_translations(domain="wtforms")


class CSRFBaseForm(BaseForm):
    class Meta:
        csrf = settings.csrf_check_enabled
        csrf_class = CSRFCookie
        csrf_cookie_name = settings.csrf_cookie_name


F = TypeVar("F", bound=BaseForm)


class FormHelper(Generic[F]):
    def __init__(
        self,
        form_class: type[F],
        template: str,
        *,
        request: Request,
        object: Any | None = None,
        data: Any | None = None,
        context: dict | None = None,
    ):
        self.form_class = form_class
        self.template = template
        self.request = request
        self.object = object
        self.data = data
        self.context: dict = {
            "request": request,
            **(context if context is not None else {}),
        }

        self._valid = True
        self._form: F | None = None

    async def get_form(self) -> F:
        if self._form:
            return self._form

        formdata = None
        if self.request.method in {"POST", "PUT", "PATCH"}:
            formdata = await self.request.form()
        self._form = self.form_class(
            formdata=formdata,
            obj=self.object,
            data=self.data,
            meta={"request": self.request},
        )
        self.context.update({"form": self._form})
        return self._form

    async def is_submitted_and_valid(self) -> bool:
        self._form = await self.get_form()
        if self.request.method in {"POST", "PUT", "PATCH"}:
            self._valid = self._form.validate()
            return self._valid
        return False

    async def get_response(self) -> _TemplateResponse:
        await self.get_form()
        status_code = status.HTTP_200_OK if self._valid else status.HTTP_400_BAD_REQUEST
        return templates.TemplateResponse(
            self.template, self.context, status_code=status_code
        )

    async def get_error_response(
        self,
        error: str,
        error_code: str,
        *,
        fatal: bool = False,
        status_code: int = status.HTTP_400_BAD_REQUEST,
    ) -> _TemplateResponse:
        self.context.update({"error": error, "fatal_error": fatal})
        return templates.TemplateResponse(
            self.template,
            self.context,
            status_code=status_code,
            headers={"X-Fief-Error": error_code},
        )


class ComboboxSelectField(HiddenField):
    def __init__(
        self,
        *args,
        query_endpoint_path: str,
        query_parameter_name: str = "query",
        value_attr: str = "id",
        label_attr: str = "name",
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.query_endpoint_path = query_endpoint_path
        self.query_parameter_name = query_parameter_name
        self.value_attr = value_attr
        self.label_attr = label_attr

    def _value(self):
        if self.data is not None:
            try:
                return getattr(self.data, self.value_attr)
            except AttributeError:
                pass
        return ""


class ComboboxSelectMultipleField(SelectMultipleField):
    def __init__(
        self,
        *args,
        query_endpoint_path: str,
        query_parameter_name: str = "query",
        value_attr: str = "id",
        label_attr: str = "name",
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.query_endpoint_path = query_endpoint_path
        self.query_parameter_name = query_parameter_name
        self.value_attr = value_attr
        self.label_attr = label_attr

    def _choices_generator(self, choices):
        if choices:
            if isinstance(choices[0], list | tuple):
                _choices = choices
            else:
                _choices = zip(choices, choices)
        else:
            _choices = []

        data_values = []
        for item in self.data or []:
            try:
                data_values.append(getattr(item, self.value_attr))
            except AttributeError:
                pass

        for value, label in _choices:
            selected = value in data_values
            yield (value, label, selected)

    def process_data(self, value):
        try:
            self.data = list(value)
        except (ValueError, TypeError):
            self.data = None


class SelectMultipleFieldCheckbox(SelectMultipleField):
    widget = widgets.ListWidget()
    option_widget = widgets.CheckboxInput()


class TimezoneField(SelectField):
    def __init__(self, *args, **kwargs):
        choices = [""] + sorted(pytz.common_timezones)
        super().__init__(*args, choices=choices, **kwargs)


def empty_string_to_none(value: str | None) -> str | None:
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
        choices = [("", "")] + [
            (country.alpha_2, country.name) for country in countries
        ]
        super().__init__(*args, choices=choices, **kwargs)


class AddressForm(BaseForm):
    def __init__(self, *args, required: bool = True, **kwargs):
        self.required = required
        super().__init__(*args, **kwargs)

    line1 = StringField(
        _("Address line 1"),
        validators=[validators.DataRequired()],
        render_kw={"autocomplete": "address-line1"},
    )
    line2 = StringField(
        _("Address line 2"),
        validators=[validators.Optional()],
        filters=[empty_string_to_none],
        render_kw={"autocomplete": "address-line2"},
    )
    postal_code = StringField(
        _("Postal code"),
        validators=[validators.DataRequired()],
        render_kw={"autocomplete": "postal-code"},
    )
    city = StringField(
        _("City"),
        validators=[validators.DataRequired()],
        render_kw={"autocomplete": "address-level2"},
    )
    state = StringField(
        _("State"),
        validators=[validators.Optional()],
        filters=[empty_string_to_none],
        render_kw={"autocomplete": "address-level1"},
    )
    country = CountryField(
        _("Country"),
        validators=[validators.DataRequired()],
        render_kw={"autocomplete": "country"},
    )

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


class PasswordValidator:
    def __init__(self) -> None:
        self.field_flags = {"password_validator": True}

    def __call__(self, form: Form, field: Field) -> Any:
        value = field.data
        if value:
            password_validation = PasswordValidation.validate(value)
            field.flags.password_strength_score = password_validation.score
            if not password_validation.valid:
                for message in password_validation.messages:
                    field.errors.append(message)
                raise validators.ValidationError()


class PasswordCreateFieldForm(BaseForm):
    password = PasswordField(
        _("Password"),
        widget=widgets.PasswordInput(hide_value=False),
        validators=[validators.InputRequired(), PasswordValidator()],
        render_kw={"autocomplete": "new-password"},
    )


USER_FIELD_FORM_FIELD_MAP: Mapping[UserFieldType, type[Field]] = {
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


def get_form_field(user_field: UserField) -> Field:
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
        field_kwargs.update(
            {"render_kw": {"placeholder": "+42102030405", "autocomplete": "tel"}}
        )
    elif user_field.type == UserFieldType.ADDRESS:
        field_kwargs.update({"required": required})
        field_kwargs.pop("validators")

    return USER_FIELD_FORM_FIELD_MAP[user_field.type](**field_kwargs)
