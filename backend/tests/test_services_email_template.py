import pytest

from fief.db import AsyncSession
from fief.services.email_template import EmailTemplateRenderer, EmailTemplateType, EmailSubjectRenderer
from fief.repositories import EmailTemplateRepository
from tests.data import TestData


@pytest.fixture
def email_template_renderer(workspace_session: AsyncSession, test_data: TestData) -> EmailTemplateRenderer:
    return EmailTemplateRenderer(EmailTemplateRepository(workspace_session))

@pytest.fixture
def email_subject_renderer(workspace_session: AsyncSession, test_data: TestData) -> EmailSubjectRenderer:
    return EmailSubjectRenderer(EmailTemplateRepository(workspace_session))


@pytest.mark.asyncio
class TestEmailTemplateRenderer:
    async def test_render_welcome(self, email_template_renderer: EmailTemplateRenderer):
        result = await email_template_renderer.render(
            EmailTemplateType.WELCOME, {"title": "TITLE"}
        )
        assert result == "<html><body><h1>TITLE</h1>WELCOME</body></html>"

    async def test_render_forgot_password(self, email_template_renderer: EmailTemplateRenderer):
        result = await email_template_renderer.render(
            EmailTemplateType.FORGOT_PASSWORD, {"title": "TITLE"}
        )
        assert result == "<html><body><h1>TITLE</h1>FORGOT_PASSWORD</body></html>"


@pytest.mark.asyncio
class TestEmailSubjectRenderer:
    async def test_render_welcome(self, email_subject_renderer: EmailTemplateRenderer):
        result = await email_subject_renderer.render(
            EmailTemplateType.WELCOME, {"title": "TITLE"}
        )
        assert result == "TITLE"

    async def test_render_forgot_password(self, email_subject_renderer: EmailTemplateRenderer):
        result = await email_subject_renderer.render(
            EmailTemplateType.FORGOT_PASSWORD, {"title": "TITLE"}
        )
        assert result == "TITLE"
