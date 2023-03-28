from wtforms import Form, IntegerField, SelectField, StringField, URLField, validators

from fief.forms import CSRFBaseForm


class ThemeCreateForm(CSRFBaseForm):
    name = StringField("Name", validators=[validators.InputRequired()])


class ThemePagePreviewForm(Form):
    page = SelectField(
        choices=[
            ("login", "Sign in"),
            ("register", "Sign up"),
            ("forgot_password", "Forgot password"),
            ("reset_password", "Reset password"),
            ("profile", "Profile"),
        ]
    )


class ThemeUpdateForm(CSRFBaseForm):
    name = StringField("Theme's name", validators=[validators.InputRequired()])

    primary_color = StringField(
        "Primary color",
        render_kw={"type": "color"},
        validators=[validators.InputRequired()],
    )
    primary_color_hover = StringField(
        "Hover primary color",
        render_kw={"type": "color"},
        validators=[validators.InputRequired()],
    )
    primary_color_light = StringField(
        "Light primary color",
        render_kw={"type": "color"},
        validators=[validators.InputRequired()],
    )

    input_color = StringField(
        "Form input text color",
        render_kw={"type": "color"},
        validators=[validators.InputRequired()],
    )
    input_color_background = StringField(
        "Form input background color",
        render_kw={"type": "color"},
        validators=[validators.InputRequired()],
    )

    light_color = StringField(
        "Light color",
        render_kw={"type": "color"},
        validators=[validators.InputRequired()],
    )
    light_color_hover = StringField(
        "Hover light color",
        render_kw={"type": "color"},
        validators=[validators.InputRequired()],
    )

    text_color = StringField(
        "Text color",
        render_kw={"type": "color"},
        validators=[validators.InputRequired()],
    )
    accent_color = StringField(
        "Accent text color",
        render_kw={"type": "color"},
        validators=[validators.InputRequired()],
    )

    background_color = StringField(
        "Background color",
        render_kw={"type": "color"},
        validators=[validators.InputRequired()],
    )

    font_size = IntegerField("Base font size", validators=[validators.InputRequired()])
    font_family = StringField("Font family", validators=[validators.InputRequired()])
    font_css_url = URLField(
        "CSS font URL",
        validators=[validators.Optional(), validators.URL(require_tld=False)],
    )
