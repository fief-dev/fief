from wtforms import BooleanField, StringField, validators

from fief.forms import CSRFBaseForm


class BaseTenantForm(CSRFBaseForm):
    name = StringField("Name", validators=[validators.InputRequired()])
    registration_allowed = BooleanField("Registration allowed")


class TenantCreateForm(BaseTenantForm):
    pass


class TenantUpdateForm(BaseTenantForm):
    pass
