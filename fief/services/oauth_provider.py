import base64
from enum import StrEnum
from typing import TYPE_CHECKING, Any

from httpx_oauth.clients.discord import DiscordOAuth2
from httpx_oauth.clients.facebook import FacebookOAuth2
from httpx_oauth.clients.github import GitHubOAuth2
from httpx_oauth.clients.google import GoogleOAuth2
from httpx_oauth.clients.linkedin import LinkedInOAuth2
from httpx_oauth.clients.microsoft import MicrosoftGraphOAuth2
from httpx_oauth.clients.openid import OpenID
from httpx_oauth.clients.reddit import RedditOAuth2
from httpx_oauth.oauth2 import BaseOAuth2

if TYPE_CHECKING:
    from fief.models import OAuthProvider


class AvailableOAuthProvider(StrEnum):
    DISCORD = "DISCORD"
    FACEBOOK = "FACEBOOK"
    GITHUB = "GITHUB"
    GOOGLE = "GOOGLE"
    LINKEDIN = "LINKEDIN"
    MICROSOFT = "MICROSOFT"
    REDDIT = "REDDIT"
    OPENID = "OPENID"

    def get_display_name(self) -> str:
        if self == AvailableOAuthProvider.OPENID:
            return "OpenID Connect"
        return getattr(OAUTH_PROVIDERS[self], "display_name", "")

    @classmethod
    def choices(cls) -> list[tuple[str, str]]:
        return [(member.value, member.get_display_name()) for member in cls]

    @classmethod
    def coerce(cls, item):
        return cls(str(item)) if not isinstance(item, cls) else item


OAUTH_PROVIDERS: dict[AvailableOAuthProvider, type[BaseOAuth2]] = {
    AvailableOAuthProvider.DISCORD: DiscordOAuth2,
    AvailableOAuthProvider.FACEBOOK: FacebookOAuth2,
    AvailableOAuthProvider.GITHUB: GitHubOAuth2,
    AvailableOAuthProvider.GOOGLE: GoogleOAuth2,
    AvailableOAuthProvider.LINKEDIN: LinkedInOAuth2,
    AvailableOAuthProvider.MICROSOFT: MicrosoftGraphOAuth2,
    AvailableOAuthProvider.REDDIT: RedditOAuth2,
    AvailableOAuthProvider.OPENID: OpenID,
}


def get_oauth_provider_branding(
    oauth_provider: "OAuthProvider",
) -> tuple[str, str | None]:
    provider_class = OAUTH_PROVIDERS[oauth_provider.provider]
    display_name: str = getattr(
        provider_class, "display_name", oauth_provider.name or ""
    )
    logo_svg: str | None = getattr(provider_class, "logo_svg", None)
    if logo_svg:
        logo_svg = base64.b64encode(logo_svg.encode("utf-8")).decode("utf-8")
    return display_name, logo_svg


def get_oauth_provider_service(oauth_provider: "OAuthProvider") -> BaseOAuth2:
    provider = oauth_provider.provider
    oauth_provider_class = OAUTH_PROVIDERS[provider]
    oauth_provider_class_kwargs: dict[str, Any] = {
        "client_id": oauth_provider.client_id,
        "client_secret": oauth_provider.client_secret,
    }
    if provider == AvailableOAuthProvider.OPENID:
        oauth_provider_class_kwargs["openid_configuration_endpoint"] = (
            oauth_provider.openid_configuration_endpoint
        )
    return oauth_provider_class(**oauth_provider_class_kwargs)
