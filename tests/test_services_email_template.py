import pytest

from fief.db import AsyncSession
from fief.repositories import EmailTemplateRepository
from fief.services.email_template.contexts import ForgotPasswordContext, WelcomeContext
from fief.services.email_template.renderers import (
    EmailSubjectRenderer,
    EmailTemplateRenderer,
)
from fief.services.email_template.types import EmailTemplateType
from tests.data import TestData


@pytest.fixture
def email_template_renderer(workspace_session: AsyncSession) -> EmailTemplateRenderer:
    return EmailTemplateRenderer(EmailTemplateRepository(workspace_session))


@pytest.fixture
def email_subject_renderer(workspace_session: AsyncSession) -> EmailSubjectRenderer:
    return EmailSubjectRenderer(EmailTemplateRepository(workspace_session))


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
