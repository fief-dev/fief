from fastapi import Depends, Request
from pydantic import ValidationError

from fief.dependencies.locale import get_translations
from fief.dependencies.tenant import get_current_tenant
from fief.exceptions import FormValidationError
from fief.locale import Translations
from fief.models import Tenant
from fief.schemas.user import UserCreate


async def get_user_create(
    request: Request,
    tenant: Tenant = Depends(get_current_tenant),
    translations: Translations = Depends(get_translations),
) -> UserCreate:
    form = await request.form()
    try:
        return UserCreate(**form)
    except ValidationError as e:
        raise FormValidationError(
            "register.html", tenant, translations, e.raw_errors, UserCreate
        ) from e
