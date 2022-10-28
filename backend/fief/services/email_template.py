from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional

import jinja2


if TYPE_CHECKING:
    from fief.models import EmailTemplate
    from fief.repositories import EmailTemplateRepository


class EmailTemplateType(str, Enum):
    BASE = "BASE"
    WELCOME = "WELCOME"
    FORGOT_PASSWORD = "FORGOT_PASSWORD"


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

    async def render(self, type: EmailTemplateType, context: Dict[str, Any]) -> str:
        jinja_environment = await self._get_jinja_environment()
        template_object = jinja_environment.get_template(type.value)
        return template_object.render(context)

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

    async def render(self, type: EmailTemplateType, context: Dict[str, Any]) -> str:
        jinja_environment = await self._get_jinja_environment()
        subject_template_object = jinja_environment.get_template(type.value)
        return subject_template_object.render(context)

    async def _get_jinja_environment(self) -> jinja2.Environment:
        if self._jinja_environment is None:
            templates = await self.repository.all()
            loader = jinja2.FunctionLoader(EmailSubjectLoader(templates))
            self._jinja_environment = jinja2.Environment(loader=loader, autoescape=True)
        return self._jinja_environment
