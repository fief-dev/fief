from wtforms import (
    BooleanField,
    FieldList,
    IntegerField,
    SelectField,
    StringField,
    validators,
)

from fief.apps.dashboard.validators import RedirectURLValidator
from fief.forms import ComboboxSelectField, CSRFBaseForm
from fief.models import ClientType


class BaseClientForm(CSRFBaseForm):
    name = StringField("Name", validators=[validators.InputRequired()])
    first_party = BooleanField("First-party")
    client_type = SelectField(
        "Type",
        choices=ClientType.get_choices(),
        default=ClientType.CONFIDENTIAL.value,
        validators=[validators.InputRequired()],
    )
    redirect_uris = FieldList(
        StringField(validators=[validators.InputRequired(), RedirectURLValidator()]),
        label="Redirect URIs",
        min_entries=1,
    )


class ClientCreateForm(BaseClientForm):
    tenant = ComboboxSelectField(
        "Tenant",
        query_endpoint_path="/admin/tenants/",
        validators=[validators.InputRequired(), validators.UUID()],
    )


class ClientUpdateForm(BaseClientForm):
    pass


class ClientLifetimesForm(CSRFBaseForm):
    authorization_code_lifetime_seconds = IntegerField(
        "Authorization code",
        description="In seconds",
        validators=[validators.InputRequired(), validators.NumberRange(min=0)],
    )
    access_id_token_lifetime_seconds = IntegerField(
        "Access and ID Token",
        description="In seconds",
        validators=[validators.InputRequired(), validators.NumberRange(min=0)],
    )
    refresh_token_lifetime_seconds = IntegerField(
        "Refresh Token",
        description="In seconds",
        validators=[validators.InputRequired(), validators.NumberRange(min=0)],
    )
