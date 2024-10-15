from typing import Any, Literal, get_args

from annotated_types import T
from httpx_oauth.exceptions import GetIdEmailError
from httpx_oauth.oauth2 import BaseOAuth2, OAuth2ClientAuthMethod


class Apple(BaseOAuth2[dict[str, Any]]):
    display_name = "Apple"
    logo_svg = """
    <svg xmlns="http://www.w3.org/2000/svg" xml:space="preserve" width="256" height="314.496" viewBox="0 0 256 314.496">
        <path d="M247.854 107.213c-1.825 1.416-34.028 19.561-34.028 59.912 0 46.671 40.978 63.183 42.204 63.59-.189 1.006-6.51 22.612-21.606 44.626-13.46 19.374-27.517 38.715-48.904 38.715s-26.89-12.424-51.576-12.424c-24.059 0-32.614 12.831-52.175 12.831s-33.211-17.925-48.904-39.941C14.687 248.673 0 208.512 0 170.394c0-61.138 39.752-93.563 78.876-93.563 20.787 0 38.116 13.65 51.169 13.65 12.424 0 31.795-14.467 55.444-14.467 8.963 0 41.167.817 62.364 31.199m-73.591-57.081c9.782-11.604 16.699-27.706 16.699-43.809 0-2.232-.189-4.498-.596-6.321-15.913.596-34.847 10.598-46.262 23.839-8.963 10.189-17.329 26.291-17.329 42.614 0 2.452.41 4.905.596 5.693 1.006.189 2.642.41 4.278.41 14.277 0 32.236-9.562 42.614-22.423"/>
    </svg>
    """
    openid_configuration = {
        "issuer": "https://appleid.apple.com",
        "authorization_endpoint": "https://appleid.apple.com/auth/authorize",
        "token_endpoint": "https://appleid.apple.com/auth/token",
        "revocation_endpoint": "https://appleid.apple.com/auth/revoke",
        "jwks_uri": "https://appleid.apple.com/auth/keys",
        "response_types_supported": ["code"],
        "response_modes_supported": ["query", "fragment", "form_post"],
        "subject_types_supported": ["pairwise"],
        "id_token_signing_alg_values_supported": ["RS256"],
        "scopes_supported": ["openid", "email", "name"],
        "token_endpoint_auth_methods_supported": ["client_secret_post"],
        "claims_supported": [
            "aud",
            "email",
            "email_verified",
            "exp",
            "iat",
            "is_private_email",
            "iss",
            "nonce",
            "nonce_supported",
            "real_user_status",
            "sub",
            "transfer_sub",
        ],
    }

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        name: str = "apple",
        base_scopes: list[str] | None = ["openid"],
    ):
        """
        Generic client for providers following the [OpenID Connect protocol](https://openid.net/connect/).

        Besides the Client ID and the Client Secret, you'll have to provide the OpenID configuration endpoint, allowing the client to discover the required endpoints automatically. By convention, it's usually served under the path `.well-known/openid-configuration`.

        Args:
            client_id: The client ID provided by the OAuth2 provider.
            client_secret: The client secret provided by the OAuth2 provider.
            openid_configuration_endpoint: OpenID Connect discovery endpoint URL.
            name: A unique name for the OAuth2 client.
            base_scopes: The base scopes to be used in the authorization URL.

        Raises:
            OpenIDConfigurationError:
                An error occurred while fetching the OpenID configuration.

        Examples:
            ```py
            from httpx_oauth.clients.openid import OpenID

            client = OpenID("CLIENT_ID", "CLIENT_SECRET", "https://example.fief.dev/.well-known/openid-configuration")
            ``
        """
        token_endpoint = self.openid_configuration["token_endpoint"]
        refresh_token_supported = "refresh_token" in self.openid_configuration.get(
            "grant_types_supported", []
        )
        revocation_endpoint = self.openid_configuration.get("revocation_endpoint")
        token_endpoint_auth_methods_supported = self.openid_configuration.get(
            "token_endpoint_auth_methods_supported", ["client_secret_basic"]
        )
        revocation_endpoint_auth_methods_supported = self.openid_configuration.get(
            "revocation_endpoint_auth_methods_supported", ["client_secret_basic"]
        )

        supported_auth_methods = get_args(OAuth2ClientAuthMethod)
        # check if there is any supported and select the first one
        token_endpoint_auth_methods_supported = [
            method
            for method in token_endpoint_auth_methods_supported
            if method in supported_auth_methods
        ]
        revocation_endpoint_auth_methods_supported = [
            method
            for method in revocation_endpoint_auth_methods_supported
            if method in supported_auth_methods
        ]

        super().__init__(
            client_id,
            client_secret,
            self.openid_configuration["authorization_endpoint"],
            token_endpoint,
            token_endpoint if refresh_token_supported else None,
            revocation_endpoint,
            name=name,
            base_scopes=base_scopes,
            token_endpoint_auth_method=token_endpoint_auth_methods_supported[0],
            revocation_endpoint_auth_method=(
                revocation_endpoint_auth_methods_supported[0]
                if revocation_endpoint
                else None
            ),
        )

    async def get_id_email(self, token: str) -> tuple[str, str | None]:
        async with self.get_httpx_client() as client:
            response = await client.get(
                self.openid_configuration["userinfo_endpoint"],
                headers={**self.request_headers, "Authorization": f"Bearer {token}"},
            )

            if response.status_code >= 400:
                raise GetIdEmailError(response=response)

            data: dict[str, Any] = response.json()

            return str(data["sub"]), data.get("email")

    async def get_authorization_url(
        self,
        redirect_uri: str,
        state: str | None = None,
        scope: list[str] | None = None,
        code_challenge: str | None = None,
        code_challenge_method: Literal["plain", "S256"] | None = None,
        extras_params: dict[str, T] | None = None,
    ):
        return await super().get_authorization_url(
            redirect_uri,
            state=state,
            scope=scope,
            code_challenge=code_challenge,
            code_challenge_method=code_challenge_method,
            extras_params=extras_params | {"response_mode": "form_post"}
            if extras_params
            else {"response_mode": "form_post"},
        )
