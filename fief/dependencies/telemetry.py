from posthog import Posthog

from fief.services.posthog import posthog


async def get_posthog() -> Posthog:
    return posthog
