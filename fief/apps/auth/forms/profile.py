from typing import TypeVar

from fastapi import Depends
from wtforms import EmailField, FormField, PasswordField, validators

from fief.dependencies.user_field import get_update_user_fields
from fief.forms import BaseForm, CSRFBaseForm, get_form_field
from fief.locale import gettext_lazy as _
from fief.models import UserField


class ChangeEmailForm(CSRFBaseForm):
    email = EmailField(
        _("Email address"), validators=[validators.InputRequired(), validators.Email()]
    )
    current_password = PasswordField(
        _("Confirm your password"),
        validators=[validators.InputRequired()],
        render_kw={"autocomplete": "current-password"},
    )


class ProfileFormBase(CSRFBaseForm):
    fields: FormField


PF = TypeVar("PF", bound=ProfileFormBase)


async def get_profile_form_class(
    update_user_fields: list[UserField] = Depends(get_update_user_fields),
) -> type[PF]:
    class ProfileFormFields(BaseForm):
        pass

    for field in update_user_fields:
        setattr(ProfileFormFields, field.slug, get_form_field(field))

    class ProfileForm(ProfileFormBase):
        fields = FormField(ProfileFormFields, separator=".")

    return ProfileForm
