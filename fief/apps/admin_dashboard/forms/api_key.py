from wtforms import StringField, validators

from fief.forms import CSRFBaseForm


class APIKeyCreateForm(CSRFBaseForm):
    name = StringField("Name", validators=[validators.InputRequired()])
