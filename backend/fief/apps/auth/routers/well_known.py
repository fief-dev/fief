from fastapi import APIRouter, Request
from fastapi.param_functions import Depends
from jwcrypto import jwk

from fief.dependencies.account import get_current_account
from fief.dependencies.tenant import get_current_tenant
from fief.models import Account, Tenant
from fief.schemas.well_known import OpenIDConfiguration
from fief.settings import settings

router = APIRouter()


@router.get("/openid-configuration", name="well_known:openid_configuration")
async def get_openid_configuration(
    request: Request,
    account: Account = Depends(get_current_account),
    tenant: Tenant = Depends(get_current_tenant),
):
    url_for_params = {}
    if not tenant.default:
        url_for_params["tenant_slug"] = tenant.slug

    def _url_for(name: str) -> str:
        return request.url_for(name, **url_for_params)

    configuration = OpenIDConfiguration(
        issuer=tenant.get_host(account.domain),
        authorization_endpoint=_url_for("auth:authorize"),
        token_endpoint=_url_for("auth:token"),
        userinfo_endpoint=_url_for("user:userinfo"),
        jwks_uri=_url_for("well_known:jwks"),
        registration_endpoint=_url_for("register:get"),
        scopes_supported=["openid", "offline_access"],
        response_types_supported=["code"],
        grant_types_supported=["authorization_code"],
        subject_types_supported=["public"],
        id_token_signing_alg_values_supported=["RS256"],
        id_token_encryption_alg_values_supported=["RSA-OAEP-256"],
        id_token_encryption_enc_values_supported=["A256CBC-HS512"],
        userinfo_signing_alg_values_supported=["none"],
        token_endpoint_auth_methods_supported=["client_secret_post"],
        claims_supported=["email", "tenant_id"],
        service_documentation=settings.fief_documentation_url,
    )

    return configuration.dict(exclude_unset=True)


@router.get("/jwks.json", name="well_known:jwks")
async def get_jwks(tenant: Tenant = Depends(get_current_tenant)):
    keyset = jwk.JWKSet(keys=tenant.get_sign_jwk())
    return keyset.export(private_keys=False, as_dict=True)
