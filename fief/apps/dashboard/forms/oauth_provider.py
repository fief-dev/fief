from wtforms import FieldList, SelectField, StringField, validators

from fief.forms import CSRFBaseForm
from fief.services.oauth_provider import AvailableOAuthProvider


class BaseOAuthProviderForm(CSRFBaseForm):
    provider = SelectField(
        "Provider",
        choices=AvailableOAuthProvider.choices(),
        coerce=AvailableOAuthProvider.coerce,
        validators=[validators.InputRequired()],
    )
    name = StringField("Name")
    openid_configuration_endpoint = StringField(
        "OpenID configuration endpoint",
        validators=[validators.InputRequired(), validators.URL()],
    )
    client_id = StringField("Client ID", validators=[validators.InputRequired()])
    client_secret = StringField(
        "Client Secret", validators=[validators.InputRequired()]
    )
    scopes = FieldList(
        StringField(validators=[validators.InputRequired()]),
        label="Scopes",
        default=[""],
    )

    def __init__(
        self, formdata=None, obj=None, prefix="", data=None, meta=None, **kwargs
    ):
        super().__init__(formdata, obj, prefix, data, meta, **kwargs)
        if self.provider.data != AvailableOAuthProvider.OPENID:
            del self.openid_configuration_endpoint


class OAuthProviderCreateForm(BaseOAuthProviderForm):
    pass


class OAuthProviderUpdateForm(BaseOAuthProviderForm):
    def __init__(
        self, formdata=None, obj=None, prefix="", data=None, meta=None, **kwargs
    ):
        super().__init__(formdata, obj, prefix, data, meta, **kwargs)
        del self.provider
