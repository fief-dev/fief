from sqlalchemy import Column, String, Text

from fief.models.base import WorkspaceBase
from fief.models.generics import CreatedUpdatedAt, UUIDModel
from fief.services.email_template.types import EmailTemplateType


class EmailTemplate(UUIDModel, CreatedUpdatedAt, WorkspaceBase):
    __tablename__ = "email_templates"

    type: EmailTemplateType = Column(String(length=255), nullable=False, unique=True)
    subject: str = Column(Text, nullable=False)
    content: str = Column(Text, nullable=False)

    def get_type_display_name(self) -> str:
        return EmailTemplateType[self.type].get_display_name()
