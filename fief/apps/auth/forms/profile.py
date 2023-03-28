from typing import TypeVar

from fastapi import Depends
from wtforms import EmailField, FormField, validators

from fief.dependencies.user_field import get_update_user_fields
from fief.forms import BaseForm, CSRFBaseForm, get_form_field
from fief.locale import gettext_lazy as _
from fief.models import UserField


class ProfileFormBase(CSRFBaseForm):
    email = EmailField(
        _("Email address"), validators=[validators.InputRequired(), validators.Email()]
    )
    fields: FormField


PF = TypeVar("PF", bound=ProfileFormBase)


async def get_profile_form_class(
    update_user_fields: list[UserField] = Depends(get_update_user_fields),
) -> type[PF]:
    class RegisterFormFields(BaseForm):
        pass

    for field in update_user_fields:
        setattr(RegisterFormFields, field.slug, get_form_field(field))

    class ProfileForm(ProfileFormBase):
        fields = FormField(RegisterFormFields, separator=".")

    return ProfileForm
