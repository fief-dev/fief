import base64
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, Optional, Tuple, Type

from httpx_oauth.clients.facebook import FacebookOAuth2
from httpx_oauth.clients.github import GitHubOAuth2
from httpx_oauth.clients.google import GoogleOAuth2
from httpx_oauth.errors import GetIdEmailError
from httpx_oauth.oauth2 import BaseOAuth2, OAuth2

if TYPE_CHECKING:
    from fief.models import OAuthProvider


class AvailableOAuthProvider(str, Enum):
    FACEBOOK = "FACEBOOK"
    GITHUB = "GITHUB"
    GOOGLE = "GOOGLE"
    CUSTOM = "CUSTOM"


OAUTH_PROVIDERS: Dict[AvailableOAuthProvider, Type[BaseOAuth2]] = {
    AvailableOAuthProvider.FACEBOOK: FacebookOAuth2,
    AvailableOAuthProvider.GITHUB: GitHubOAuth2,
    AvailableOAuthProvider.GOOGLE: GoogleOAuth2,
    AvailableOAuthProvider.CUSTOM: OAuth2,
}


def get_oauth_provider_branding(
    oauth_provider: "OAuthProvider",
) -> Tuple[str, Optional[str]]:
    provider_class = OAUTH_PROVIDERS[oauth_provider.provider]
    display_name: str = getattr(
        provider_class, "display_name", oauth_provider.name or ""
    )
    logo_svg: Optional[str] = getattr(provider_class, "logo_svg", None)
    if logo_svg:
        logo_svg = base64.b64encode(logo_svg.encode("utf-8")).decode("utf-8")
    return display_name, logo_svg


def get_oauth_provider_service(oauth_provider: "OAuthProvider") -> BaseOAuth2:
    provider = oauth_provider.provider
    oauth_provider_class = OAUTH_PROVIDERS[provider]
    oauth_provider_class_kwargs: Dict[str, Any] = {
        "client_id": oauth_provider.client_id,
        "client_secret": oauth_provider.client_secret,
    }
    if provider == AvailableOAuthProvider.CUSTOM:
        oauth_provider_class_kwargs[
            "authorize_endpoint"
        ] = oauth_provider.authorize_endpoint
        oauth_provider_class_kwargs[
            "access_token_endpoint"
        ] = oauth_provider.access_token_endpoint
        oauth_provider_class_kwargs[
            "refresh_token_endpoint"
        ] = oauth_provider.refresh_token_endpoint
        oauth_provider_class_kwargs[
            "revoke_token_endpoint"
        ] = oauth_provider.revoke_token_endpoint
    return oauth_provider_class(**oauth_provider_class_kwargs)


async def get_oauth_id_email(
    oauth_provider: "OAuthProvider", access_token: str
) -> Tuple[str, str]:
    oauth_provider_service = get_oauth_provider_service(oauth_provider)

    try:
        return await oauth_provider_service.get_id_email(access_token)
    except (NotImplementedError, GetIdEmailError) as e:
        raise


__all__ = ["OAUTH_PROVIDERS", "AvailableOAuthProvider", "BaseOAuth2"]
