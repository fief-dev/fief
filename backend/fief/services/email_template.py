from enum import Enum
from typing import TYPE_CHECKING, Dict, List, Literal, Optional, overload

import jinja2
from pydantic import BaseModel

from fief.schemas.tenant import Tenant
from fief.schemas.user import UserRead

if TYPE_CHECKING:  # pragma: no cover
    from fief.models import EmailTemplate
    from fief.repositories import EmailTemplateRepository


class EmailTemplateType(str, Enum):
    BASE = "BASE"
    WELCOME = "WELCOME"
    FORGOT_PASSWORD = "FORGOT_PASSWORD"


class EmailContext(BaseModel):
    tenant: Tenant
    user: UserRead

    class Config:
        orm_mode = True


class WelcomeContext(EmailContext):
    pass


class ForgotPasswordContext(EmailContext):
    reset_url: str


def _templates_list_to_map(
    templates: List["EmailTemplate"],
) -> Dict[str, "EmailTemplate"]:
    return {template.type: template for template in templates}


class EmailTemplateLoader:
    def __init__(self, templates: List["EmailTemplate"]):
        self.templates_map = _templates_list_to_map(templates)

    def __call__(self, name: str) -> str:
        return self.templates_map[name].content


class EmailTemplateRenderer:
    def __init__(self, repository: "EmailTemplateRepository"):
        self.repository = repository
        self._jinja_environment: Optional[jinja2.Environment] = None

    @overload
    async def render(
        self, type: Literal[EmailTemplateType.WELCOME], context: WelcomeContext
    ) -> str:
        ...  # pragma: no cover

    @overload
    async def render(
        self,
        type: Literal[EmailTemplateType.FORGOT_PASSWORD],
        context: ForgotPasswordContext,
    ) -> str:
        ...  # pragma: no cover

    async def render(self, type, context: EmailContext) -> str:
        jinja_environment = await self._get_jinja_environment()
        template_object = jinja_environment.get_template(type.value)
        return template_object.render(context.dict())

    async def _get_jinja_environment(self) -> jinja2.Environment:
        if self._jinja_environment is None:
            templates = await self.repository.all()
            loader = jinja2.FunctionLoader(EmailTemplateLoader(templates))
            self._jinja_environment = jinja2.Environment(loader=loader, autoescape=True)
        return self._jinja_environment


class EmailSubjectLoader:
    def __init__(self, templates: List["EmailTemplate"]):
        self.templates_map = _templates_list_to_map(templates)

    def __call__(self, name: str) -> str:
        return self.templates_map[name].subject


class EmailSubjectRenderer:
    def __init__(self, repository: "EmailTemplateRepository"):
        self.repository = repository
        self._jinja_environment: Optional[jinja2.Environment] = None

    @overload
    async def render(
        self, type: Literal[EmailTemplateType.WELCOME], context: WelcomeContext
    ) -> str:
        ...  # pragma: no cover

    @overload
    async def render(
        self,
        type: Literal[EmailTemplateType.FORGOT_PASSWORD],
        context: ForgotPasswordContext,
    ) -> str:
        ...  # pragma: no cover

    async def render(self, type, context: EmailContext) -> str:
        jinja_environment = await self._get_jinja_environment()
        subject_template_object = jinja_environment.get_template(type.value)
        return subject_template_object.render(context.dict())

    async def _get_jinja_environment(self) -> jinja2.Environment:
        if self._jinja_environment is None:
            templates = await self.repository.all()
            loader = jinja2.FunctionLoader(EmailSubjectLoader(templates))
            self._jinja_environment = jinja2.Environment(loader=loader, autoescape=True)
        return self._jinja_environment
