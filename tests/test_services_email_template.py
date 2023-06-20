import jinja2
import pytest

from fief.db import AsyncSession
from fief.models import EmailTemplate
from fief.repositories import EmailTemplateRepository
from fief.services.email_template.contexts import (
    ForgotPasswordContext,
    VerifyEmailContext,
    WelcomeContext,
)
from fief.services.email_template.renderers import (
    EmailSubjectRenderer,
    EmailTemplateRenderer,
)
from fief.services.email_template.types import EmailTemplateType
from tests.data import TestData


@pytest.fixture
def email_template_repository(
    workspace_session: AsyncSession,
) -> EmailTemplateRepository:
    return EmailTemplateRepository(workspace_session)


@pytest.fixture
def email_template_renderer(
    email_template_repository: EmailTemplateRepository,
) -> EmailTemplateRenderer:
    return EmailTemplateRenderer(email_template_repository)


@pytest.fixture
def email_subject_renderer(
    email_template_repository: EmailTemplateRepository,
) -> EmailSubjectRenderer:
    return EmailSubjectRenderer(email_template_repository)


UNSAFE_COMMANDS = [
    "{{ cycler.__init__.__globals__.os.popen('id').read() }}",
    "{{ foo.__init__.bar }}",
]


@pytest.mark.asyncio
class TestEmailTemplateRenderer:
    async def test_render_welcome(
        self, email_template_renderer: EmailTemplateRenderer, test_data: TestData
    ):
        context = WelcomeContext(
            tenant=test_data["tenants"]["default"], user=test_data["users"]["regular"]
        )
        result = await email_template_renderer.render(
            EmailTemplateType.WELCOME, context
        )
        assert result == "<html><body><h1>Default</h1>WELCOME</body></html>"

    async def test_render_verify_email(
        self, email_template_renderer: EmailTemplateRenderer, test_data: TestData
    ):
        context = VerifyEmailContext(
            tenant=test_data["tenants"]["default"],
            user=test_data["users"]["regular"],
            code="ABCDEF",
        )
        result = await email_template_renderer.render(
            EmailTemplateType.VERIFY_EMAIL, context
        )
        assert result == "<html><body><h1>Default</h1>VERIFY_EMAIL ABCDEF</body></html>"

    async def test_render_forgot_password(
        self, email_template_renderer: EmailTemplateRenderer, test_data: TestData
    ):
        context = ForgotPasswordContext(
            tenant=test_data["tenants"]["default"],
            reset_url="http://bretagne.fief.dev/reset",
            user=test_data["users"]["regular"],
        )
        result = await email_template_renderer.render(
            EmailTemplateType.FORGOT_PASSWORD, context
        )
        assert (
            result
            == "<html><body><h1>Default</h1>FORGOT_PASSWORD http://bretagne.fief.dev/reset</body></html>"
        )

    @pytest.mark.parametrize("command", UNSAFE_COMMANDS)
    async def test_prevent_unsafe_commands(
        self,
        command: str,
        email_template_repository: EmailTemplateRepository,
        test_data: TestData,
    ):
        email_template = EmailTemplate(
            type=EmailTemplateType.FORGOT_PASSWORD,
            subject="TITLE",
            content=command,
        )

        email_template_renderer = EmailTemplateRenderer(
            email_template_repository,
            templates_overrides={EmailTemplateType.FORGOT_PASSWORD: email_template},
        )
        context = ForgotPasswordContext(
            tenant=test_data["tenants"]["default"],
            reset_url="http://bretagne.fief.dev/reset",
            user=test_data["users"]["regular"],
        )
        with pytest.raises(jinja2.exceptions.SecurityError):
            await email_template_renderer.render(
                EmailTemplateType.FORGOT_PASSWORD, context
            )


@pytest.mark.asyncio
class TestEmailSubjectRenderer:
    async def test_render_welcome(
        self, email_subject_renderer: EmailTemplateRenderer, test_data: TestData
    ):
        context = WelcomeContext(
            tenant=test_data["tenants"]["default"], user=test_data["users"]["regular"]
        )
        result = await email_subject_renderer.render(EmailTemplateType.WELCOME, context)
        assert result == "TITLE"

    async def test_render_verify_email(
        self, email_subject_renderer: EmailTemplateRenderer, test_data: TestData
    ):
        context = VerifyEmailContext(
            tenant=test_data["tenants"]["default"],
            user=test_data["users"]["regular"],
            code="ABCDEF",
        )
        result = await email_subject_renderer.render(
            EmailTemplateType.VERIFY_EMAIL, context
        )
        assert result == "TITLE"

    async def test_render_forgot_password(
        self, email_subject_renderer: EmailTemplateRenderer, test_data: TestData
    ):
        context = ForgotPasswordContext(
            tenant=test_data["tenants"]["default"],
            reset_url="http://bretagne.fief.dev/reset",
            user=test_data["users"]["regular"],
        )
        result = await email_subject_renderer.render(
            EmailTemplateType.FORGOT_PASSWORD, context
        )
        assert result == "TITLE"

    @pytest.mark.parametrize("command", UNSAFE_COMMANDS)
    async def test_prevent_access_to_magic_methods_from_undefined_object(
        self,
        command: str,
        email_template_repository: EmailTemplateRepository,
        test_data: TestData,
    ):
        email_template = EmailTemplate(
            type=EmailTemplateType.FORGOT_PASSWORD,
            subject=command,
            content="",
        )

        email_subject_renderer = EmailSubjectRenderer(
            email_template_repository,
            templates_overrides={EmailTemplateType.FORGOT_PASSWORD: email_template},
        )
        context = ForgotPasswordContext(
            tenant=test_data["tenants"]["default"],
            reset_url="http://bretagne.fief.dev/reset",
            user=test_data["users"]["regular"],
        )
        with pytest.raises(jinja2.exceptions.SecurityError):
            await email_subject_renderer.render(
                EmailTemplateType.FORGOT_PASSWORD, context
            )
