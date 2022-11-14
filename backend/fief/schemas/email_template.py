from typing import Optional

from fief.schemas.generics import BaseModel, CreatedUpdatedAt, UUIDSchema
from fief.services.email_template.types import EmailTemplateType


class EmailTemplateUpdate(BaseModel):
    subject: Optional[str]
    content: Optional[str]


class EmailTemplateBase(UUIDSchema, CreatedUpdatedAt):
    type: EmailTemplateType
    subject: str
    content: str


class EmailTemplate(EmailTemplateBase):
    pass


class EmailTemplatePreviewInput(BaseModel):
    type: EmailTemplateType
    subject: str
    content: str


class EmailTemplatePreviewResult(BaseModel):
    subject: str
    content: str
