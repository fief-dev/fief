from fief.schemas.generics import BaseModel, CreatedUpdatedAt, UUIDSchema
from fief.services.email_template.types import EmailTemplateType


class EmailTemplateUpdate(BaseModel):
    subject: str | None
    content: str | None


class EmailTemplateBase(UUIDSchema, CreatedUpdatedAt):
    type: EmailTemplateType
    subject: str
    content: str


class EmailTemplate(EmailTemplateBase):
    pass
