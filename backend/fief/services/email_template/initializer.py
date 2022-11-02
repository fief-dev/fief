from pathlib import Path

from fief.models import EmailTemplate
from fief.repositories.email_template import EmailTemplateRepository
from fief.services.email_template.types import EmailTemplateType


class EmailTemplateInitializer:
    def __init__(self, repository: EmailTemplateRepository):
        self.repository = repository
        self.templates_dir = Path(__file__).parent / "templates"

    async def init_templates(self):
        base = EmailTemplate(
            type=EmailTemplateType.BASE,
            subject="",
            content=self._load_template("base.html"),
        )
        await self.repository.create(base)

        welcome = EmailTemplate(
            type=EmailTemplateType.WELCOME,
            subject="Welcome to {{ tenant.name }}",
            content=self._load_template("welcome.html"),
        )
        await self.repository.create(welcome)

        forgot_password = EmailTemplate(
            type=EmailTemplateType.FORGOT_PASSWORD,
            subject="Reset your {{ tenant.name }}'s password",
            content=self._load_template("forgot_password.html"),
        )
        await self.repository.create(forgot_password)

    def _load_template(self, name: str) -> str:
        with open(self.templates_dir / name, "r") as file:
            return file.read()
