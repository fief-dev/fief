from typing import TYPE_CHECKING, Literal, overload

import jinja2

from fief.services.email_template.types import EmailTemplateType

if TYPE_CHECKING:  # pragma: no cover
    from fief.models import EmailTemplate
    from fief.repositories import EmailTemplateRepository
    from fief.services.email_template.contexts import (
        EmailContext,
        ForgotPasswordContext,
        WelcomeContext,
    )


def _templates_list_to_map(
    templates: list["EmailTemplate"],
) -> dict[str, "EmailTemplate"]:
    return {template.type: template for template in templates}


class EmailTemplateLoader:
    def __init__(
        self,
        templates: list["EmailTemplate"],
        *,
        templates_overrides: dict[EmailTemplateType, "EmailTemplate"] | None = None,
    ):
        self.templates_map = _templates_list_to_map(templates)
        if templates_overrides:
            for type, template in templates_overrides.items():
                self.templates_map[type] = template

    def __call__(self, name: str) -> str:
        return self.templates_map[name].content


class EmailTemplateRenderer:
    def __init__(
        self,
        repository: "EmailTemplateRepository",
        *,
        templates_overrides: dict[EmailTemplateType, "EmailTemplate"] | None = None,
    ):
        self.repository = repository
        self._jinja_environment: jinja2.Environment | None = None
        self.templates_overrides = templates_overrides

    @overload
    async def render(
        self, type: Literal[EmailTemplateType.WELCOME], context: "WelcomeContext"
    ) -> str:
        ...  # pragma: no cover

    @overload
    async def render(
        self,
        type: Literal[EmailTemplateType.FORGOT_PASSWORD],
        context: "ForgotPasswordContext",
    ) -> str:
        ...  # pragma: no cover

    async def render(self, type, context: "EmailContext") -> str:
        jinja_environment = await self._get_jinja_environment()
        template_object = jinja_environment.get_template(type.value)
        return template_object.render(context.dict())

    async def _get_jinja_environment(self) -> jinja2.Environment:
        if self._jinja_environment is None:
            templates = await self.repository.all()
            loader = jinja2.FunctionLoader(
                EmailTemplateLoader(
                    templates, templates_overrides=self.templates_overrides
                )
            )
            self._jinja_environment = jinja2.Environment(loader=loader, autoescape=True)
        return self._jinja_environment


class EmailSubjectLoader:
    def __init__(
        self,
        templates: list["EmailTemplate"],
        *,
        templates_overrides: dict[EmailTemplateType, "EmailTemplate"] | None = None,
    ):
        self.templates_map = _templates_list_to_map(templates)
        if templates_overrides:
            for type, template in templates_overrides.items():
                self.templates_map[type] = template

    def __call__(self, name: str) -> str:
        return self.templates_map[name].subject


class EmailSubjectRenderer:
    def __init__(
        self,
        repository: "EmailTemplateRepository",
        *,
        templates_overrides: dict[EmailTemplateType, "EmailTemplate"] | None = None,
    ):
        self.repository = repository
        self._jinja_environment: jinja2.Environment | None = None
        self.templates_overrides = templates_overrides

    @overload
    async def render(
        self, type: Literal[EmailTemplateType.WELCOME], context: "WelcomeContext"
    ) -> str:
        ...  # pragma: no cover

    @overload
    async def render(
        self,
        type: Literal[EmailTemplateType.FORGOT_PASSWORD],
        context: "ForgotPasswordContext",
    ) -> str:
        ...  # pragma: no cover

    async def render(self, type, context: "EmailContext") -> str:
        jinja_environment = await self._get_jinja_environment()
        subject_template_object = jinja_environment.get_template(type.value)
        return subject_template_object.render(context.dict())

    async def _get_jinja_environment(self) -> jinja2.Environment:
        if self._jinja_environment is None:
            templates = await self.repository.all()
            loader = jinja2.FunctionLoader(
                EmailSubjectLoader(
                    templates, templates_overrides=self.templates_overrides
                )
            )
            self._jinja_environment = jinja2.Environment(loader=loader, autoescape=True)
        return self._jinja_environment
