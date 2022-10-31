from typing import Optional

from fief.schemas.generics import BaseModel, CreatedUpdatedAt, UUIDSchema
from fief.services.email_template import EmailTemplateType


class EmailTemplateUpdate(BaseModel):
    subject: Optional[str]
    content: Optional[str]


class EmailTemplateBase(UUIDSchema, CreatedUpdatedAt):
    type: EmailTemplateType
    subject: Optional[str]
    content: str


class EmailTemplate(EmailTemplateBase):
    pass
