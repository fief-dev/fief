import uuid
from wtforms import validators, StringField, BooleanField, SelectField, FieldList

from fief.forms import CSRFBaseForm, ComboboxSelectField
from fief.models import ClientType
from fief.apps.admin_htmx.validators import RedirectURLValidator


class ClientCreateForm(CSRFBaseForm):
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
    tenant_id = ComboboxSelectField(
        "Tenant",
        query_endpoint_path="/admin/tenants/",
        validators=[validators.InputRequired(), validators.UUID()],
    )
