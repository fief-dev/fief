from typing import List, Optional

from pydantic import AnyUrl, BaseModel


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
    scopes_supported: List[str]
    response_types_supported: List[str]
    response_modes_supported: Optional[List[str]] = None
    grant_types_supported: Optional[List[str]] = None
    token_endpoint_auth_methods_supported: Optional[List[str]] = None
    token_endpoint_auth_signing_alg_values_supported: Optional[List[str]] = None
    service_documentation: Optional[AnyUrl] = None
    ui_locales_supported: Optional[List[str]] = None
    op_policy_uri: Optional[AnyUrl] = None
    op_tos_uri: Optional[AnyUrl] = None
    revocation_endpoint: Optional[AnyUrl] = None
    revocation_endpoint_auth_methods_supported: Optional[List[str]] = None
    revocation_endpoint_auth_signing_alg_values_supported: Optional[List[str]] = None
    introspection_endpoint: Optional[AnyUrl] = None
    introspection_endpoint_auth_methods_supported: Optional[List[str]] = None
    introspection_endpoint_auth_signing_alg_values_supported: Optional[List[str]] = None
    code_challenge_methods_supported: Optional[List[str]] = None


class OpenIDProviderMetadata(OAuth2AuthorizationServerMetadata):
    """
    OpenID Provider Metadata

    Conforms to OpenID Connect Discovery 1.0 specification.
    https://openid.net/specs/openid-connect-discovery-1_0.html#ProviderMetadata
    """

    userinfo_endpoint: AnyUrl
    acr_values_supported: Optional[List[str]] = None
    subject_types_supported: List[str]
    id_token_signing_alg_values_supported: List[str]
    id_token_encryption_alg_values_supported: Optional[List[str]] = None
    id_token_encryption_enc_values_supported: Optional[List[str]] = None
    userinfo_signing_alg_values_supported: Optional[List[str]] = None
    userinfo_encryption_alg_values_supported: Optional[List[str]] = None
    userinfo_encryption_enc_values_supported: Optional[List[str]] = None
    request_object_signing_alg_values_supported: Optional[List[str]] = None
    request_object_encryption_alg_values_supported: Optional[List[str]] = None
    request_object_encryption_enc_values_supported: Optional[List[str]] = None
    token_endpoint_auth_methods_supported: Optional[List[str]] = None
    token_endpoint_auth_signing_alg_values_supported: Optional[List[str]] = None
    display_values_supported: Optional[List[str]] = None
    claim_types_supported: Optional[List[str]] = None
    claims_supported: Optional[List[str]] = None
    claims_locales_supported: Optional[List[str]] = None
    claims_parameter_supported: Optional[bool] = None
    request_parameter_supported: Optional[bool] = None
    request_uri_parameter_supported: Optional[bool] = None
    require_request_uri_registration: Optional[bool] = None
