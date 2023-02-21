from wtforms import StringField, validators

from fief.forms import CSRFBaseForm


class PermissionCreateForm(CSRFBaseForm):
    name = StringField(
        "Name",
        validators=[validators.InputRequired()],
        render_kw={"placeholder": "Create Castle"},
    )
    codename = StringField(
        "Codename",
        validators=[validators.InputRequired()],
        render_kw={"placeholder": "castles:create"},
    )
