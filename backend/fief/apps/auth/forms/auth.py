from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from wtforms import EmailField, PasswordField, SubmitField, validators

from fief.apps.auth.forms.base import CSRFBaseForm
from fief.locale import gettext_lazy as _


class LoginForm(CSRFBaseForm):
    email = EmailField(
        _("Email address"), validators=[validators.InputRequired(), validators.Email()]
    )
    password = PasswordField(_("Password"), validators=[validators.InputRequired()])

    def get_credentials(self) -> OAuth2PasswordRequestForm:
        return OAuth2PasswordRequestForm(
            username=self.email.data,
            password=self.password.data,
            grant_type="password",
            scope="",
        )


class ConsentForm(CSRFBaseForm):
    allow = SubmitField(_("Allow"))
    deny = SubmitField(_("Deny"))
