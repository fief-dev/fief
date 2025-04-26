from fief.settings import settings


async def get_show_branding() -> bool:
    return settings.branding
