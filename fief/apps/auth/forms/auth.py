from wtforms import EmailField, HiddenField, PasswordField, SubmitField, validators

from fief.forms import CSRFBaseForm
from fief.locale import gettext_lazy as _


class LoginForm(CSRFBaseForm):
    email = EmailField(
        _("Email address"), validators=[validators.InputRequired(), validators.Email()]
    )
    password = PasswordField(_("Password"), validators=[validators.InputRequired()])


class VerifyEmailForm(CSRFBaseForm):
    code = HiddenField(_("Verification code"), validators=[validators.InputRequired()])


class ConsentForm(CSRFBaseForm):
    allow = SubmitField(_("Allow"))
    deny = SubmitField(_("Deny"))
