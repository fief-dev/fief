from enum import Enum
from typing import Dict, Type

from httpx_oauth.clients.facebook import FacebookOAuth2
from httpx_oauth.clients.github import GitHubOAuth2
from httpx_oauth.clients.google import GoogleOAuth2
from httpx_oauth.oauth2 import BaseOAuth2, OAuth2


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
