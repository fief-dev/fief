import secrets
from typing import Generic, Optional, Type, TypeVar

from fastapi import Request, status
from starlette.templating import _TemplateResponse
from wtforms import Field, Form, validators
from wtforms.csrf.core import CSRF

from fief.apps.auth.templates import templates
from fief.locale import get_translations
from fief.middlewares.csrf import CSRF_ATTRIBUTE_NAME
from fief.settings import settings


class CSRFCookieMissingRequest(TypeError):
    def __init__(self) -> None:
        super().__init__("Must provide a Request object for CSRF to work.")


class CSRFCookie(CSRF):
    def setup_form(self, form: Form):
        self.form_meta = form.meta
        return super().setup_form(form)

    def generate_csrf_token(self, csrf_token_field: Field):
        csrf_token: Optional[str] = self.get_challenge_csrf_token()
        if csrf_token is None:
            csrf_token = secrets.token_urlsafe()
            # Will be catched by CSRFCookieSetterMiddleware and set in cookies
            self.request.scope[CSRF_ATTRIBUTE_NAME] = csrf_token

        return csrf_token

    def validate_csrf_token(self, form: Form, field: Field):
        challenge_csrf_token = self.get_challenge_csrf_token()
        if (
            field.data is None
            or challenge_csrf_token is None
            or not secrets.compare_digest(field.data, challenge_csrf_token)
        ):
            raise validators.ValidationError(field.gettext("CSRF failed."))

    def get_challenge_csrf_token(self) -> Optional[str]:
        return self.request.cookies.get(self.form_meta.csrf_cookie_name)

    @property
    def request(self) -> Request:
        try:
            return getattr(self.form_meta, "request")
        except AttributeError as e:
            raise CSRFCookieMissingRequest() from e


class BaseForm(Form):
    class Meta:
        def get_translations(self, form):
            return get_translations(domain="wtforms")


class CSRFBaseForm(BaseForm):
    class Meta:
        csrf = settings.csrf_check_enabled
        csrf_class = CSRFCookie
        csrf_cookie_name = settings.csrf_cookie_name


F = TypeVar("F", bound=BaseForm)


class FormHelper(Generic[F]):
    def __init__(
        self,
        form_class: Type[F],
        template: str,
        *,
        request: Request,
        context: Optional[dict] = None
    ):
        self.form_class = form_class
        self.template = template
        self.request = request
        self.context: dict = {
            "request": request,
            **(context if context is not None else {}),
        }

        self._valid = True
        self._form: Optional[F] = None

    async def get_form(self) -> F:
        if self._form:
            return self._form

        self._form = self.form_class(
            await self.request.form(), meta={"request": self.request}
        )
        self.context.update({"form": self._form})
        return self._form

    async def is_submitted_and_valid(self) -> bool:
        self._form = await self.get_form()
        if self.request.method == "POST":
            self._valid = self._form.validate()
            return self._valid
        return False

    async def get_response(self) -> _TemplateResponse:
        status_code = status.HTTP_200_OK if self._valid else status.HTTP_400_BAD_REQUEST
        return templates.TemplateResponse(
            self.template, self.context, status_code=status_code
        )

    async def get_error_response(
        self,
        error: str,
        error_code: str,
        *,
        fatal: bool = False,
        status_code: int = status.HTTP_400_BAD_REQUEST
    ) -> _TemplateResponse:
        self.context.update({"error": error, "fatal_error": fatal})
        return templates.TemplateResponse(
            self.template,
            self.context,
            status_code=status_code,
            headers={"X-Fief-Error": error_code},
        )
