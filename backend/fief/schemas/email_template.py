from typing import Optional

from fief.schemas.generics import BaseModel, CreatedUpdatedAt, UUIDSchema
from fief.services.email_template.contexts import EmailTemplateType


class EmailTemplateUpdate(BaseModel):
    subject: Optional[str]
    content: Optional[str]


class EmailTemplateBase(UUIDSchema, CreatedUpdatedAt):
    type: EmailTemplateType
    subject: Optional[str]
    content: str


class EmailTemplate(EmailTemplateBase):
    pass


class EmailTemplatePreview(BaseModel):
    subject: str
    content: str
