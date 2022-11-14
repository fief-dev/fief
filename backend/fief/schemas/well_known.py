from pydantic import AnyUrl

from fief.schemas.generics import BaseModel


class OAuth2AuthorizationServerMetadata(BaseModel):
    """
    OAuth 2.0 Authorization Server Metadata

    Conforms to RFC8414.
    https://datatracker.ietf.org/doc/html/rfc8414
    """

    issuer: AnyUrl
    authorization_endpoint: AnyUrl
    token_endpoint: AnyUrl
    jwks_uri: AnyUrl
    registration_endpoint: AnyUrl
    scopes_supported: list[str]
    response_types_supported: list[str]
    response_modes_supported: list[str] | None = None
    grant_types_supported: list[str] | None = None
    token_endpoint_auth_methods_supported: list[str] | None = None
    token_endpoint_auth_signing_alg_values_supported: list[str] | None = None
    service_documentation: AnyUrl | None = None
    ui_locales_supported: list[str] | None = None
    op_policy_uri: AnyUrl | None = None
    op_tos_uri: AnyUrl | None = None
    revocation_endpoint: AnyUrl | None = None
    revocation_endpoint_auth_methods_supported: list[str] | None = None
    revocation_endpoint_auth_signing_alg_values_supported: list[str] | None = None
    introspection_endpoint: AnyUrl | None = None
    introspection_endpoint_auth_methods_supported: list[str] | None = None
    introspection_endpoint_auth_signing_alg_values_supported: list[str] | None = None
    code_challenge_methods_supported: list[str] | None = None


class OpenIDProviderMetadata(OAuth2AuthorizationServerMetadata):
    """
    OpenID Provider Metadata

    Conforms to OpenID Connect Discovery 1.0 specification.
    https://openid.net/specs/openid-connect-discovery-1_0.html#ProviderMetadata
    """

    userinfo_endpoint: AnyUrl
    acr_values_supported: list[str] | None = None
    subject_types_supported: list[str]
    id_token_signing_alg_values_supported: list[str]
    id_token_encryption_alg_values_supported: list[str] | None = None
    id_token_encryption_enc_values_supported: list[str] | None = None
    userinfo_signing_alg_values_supported: list[str] | None = None
    userinfo_encryption_alg_values_supported: list[str] | None = None
    userinfo_encryption_enc_values_supported: list[str] | None = None
    request_object_signing_alg_values_supported: list[str] | None = None
    request_object_encryption_alg_values_supported: list[str] | None = None
    request_object_encryption_enc_values_supported: list[str] | None = None
    token_endpoint_auth_methods_supported: list[str] | None = None
    token_endpoint_auth_signing_alg_values_supported: list[str] | None = None
    display_values_supported: list[str] | None = None
    claim_types_supported: list[str] | None = None
    claims_supported: list[str] | None = None
    claims_locales_supported: list[str] | None = None
    claims_parameter_supported: bool | None = None
    request_parameter_supported: bool | None = None
    request_uri_parameter_supported: bool | None = None
    require_request_uri_registration: bool | None = None
