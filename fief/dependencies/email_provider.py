from fief.services.email import EmailProvider
from fief.settings import settings


async def get_email_provider() -> EmailProvider:
    return settings.get_email_provider()
