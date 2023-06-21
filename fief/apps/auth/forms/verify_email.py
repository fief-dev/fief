from wtforms import HiddenField, validators

from fief.forms import CSRFBaseForm
from fief.locale import gettext_lazy as _


class VerifyEmailForm(CSRFBaseForm):
    code = HiddenField(_("Verification code"), validators=[validators.InputRequired()])

    class Meta:
        id = "verify-email-form"
