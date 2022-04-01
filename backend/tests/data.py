import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Mapping, Tuple, TypedDict

from fief.crypto.code_challenge import get_code_verifier_hash
from fief.crypto.id_token import get_validation_hash
from fief.crypto.jwk import generate_jwk
from fief.crypto.password import password_helper
from fief.crypto.token import generate_token
from fief.models import (
    AuthorizationCode,
    Client,
    Grant,
    LoginSession,
    M,
    RefreshToken,
    SessionToken,
    Tenant,
    User,
)
from fief.settings import settings

ModelMapping = Mapping[str, M]

now = datetime.now(timezone.utc)


class TestData(TypedDict):
    __test__ = False

    tenants: ModelMapping[Tenant]
    clients: ModelMapping[Client]
    users: ModelMapping[User]
    login_sessions: ModelMapping[LoginSession]
    authorization_codes: ModelMapping[AuthorizationCode]
    refresh_tokens: ModelMapping[RefreshToken]
    session_tokens: ModelMapping[SessionToken]
    grants: ModelMapping[Grant]


tenants: ModelMapping[Tenant] = {
    "default": Tenant(name="Default", slug="default", default=True),
    "secondary": Tenant(name="Secondary", slug="secondary", default=False),
}

clients: ModelMapping[Client] = {
    "default_tenant": Client(
        name="Default",
        tenant=tenants["default"],
        client_id="DEFAULT_TENANT_CLIENT_ID",
        client_secret="DEFAULT_TENANT_CLIENT_SECRET",
        redirect_uris=["https://nantes.city/callback"],
    ),
    "granted_default_tenant": Client(
        name="Granted default",
        tenant=tenants["default"],
        client_id="GRANTED_DEFAULT_TENANT_CLIENT_ID",
        client_secret="GRANTED_DEFAULT_TENANT_CLIENT_SECRET",
        redirect_uris=["https://nantes.city/callback"],
    ),
    "first_party_default_tenant": Client(
        name="First-party default",
        first_party=True,
        tenant=tenants["default"],
        client_id="FIRST_PARTY_DEFAULT_TENANT_CLIENT_ID",
        client_secret="FIRST_PARTY_DEFAULT_TENANT_CLIENT_SECRET",
        redirect_uris=["https://nantes.city/callback"],
    ),
    "encryption_default_tenant": Client(
        name="Encryption default",
        tenant=tenants["default"],
        client_id="ENCRYPTION_DEFAULT_TENANT_CLIENT_ID",
        client_secret="ENCRYPTION_DEFAULT_TENANT_CLIENT_SECRET",
        encrypt_jwk=generate_jwk(secrets.token_urlsafe(), "enc").export_public(),
        redirect_uris=["https://nantes.city/callback"],
    ),
    "secondary_tenant": Client(
        name="Secondary",
        tenant=tenants["secondary"],
        redirect_uris=["https://nantes.city/callback"],
    ),
}

users: ModelMapping[User] = {
    "regular": User(
        id=uuid.uuid4(),
        email="anne@bretagne.duchy",
        hashed_password=password_helper.hash("hermine"),
        tenant=tenants["default"],
    ),
    "regular_secondary": User(
        id=uuid.uuid4(),
        email="anne@nantes.city",
        hashed_password=password_helper.hash("hermine"),
        tenant=tenants["secondary"],
    ),
}

login_sessions: ModelMapping[LoginSession] = {
    "default": LoginSession(
        response_type="code",
        response_mode="query",
        redirect_uri="https://nantes.city/callback",
        scope=["openid", "offline_access"],
        state="STATE",
        nonce="NONCE",
        client=clients["default_tenant"],
    ),
    "default_none_prompt": LoginSession(
        response_type="code",
        response_mode="query",
        redirect_uri="https://nantes.city/callback",
        scope=["openid", "offline_access"],
        state="STATE",
        nonce="NONCE",
        client=clients["default_tenant"],
        prompt="none",
    ),
    "default_code_challenge_plain": LoginSession(
        response_type="code",
        response_mode="query",
        redirect_uri="https://nantes.city/callback",
        scope=["openid", "offline_access"],
        state="STATE",
        code_challenge="PLAIN_CODE_CHALLENGE",
        code_challenge_method="plain",
        client=clients["default_tenant"],
    ),
    "default_code_challenge_s256": LoginSession(
        response_type="code",
        response_mode="query",
        redirect_uri="https://nantes.city/callback",
        scope=["openid", "offline_access"],
        state="STATE",
        code_challenge=get_code_verifier_hash("S256_CODE_CHALLENGE"),
        code_challenge_method="S256",
        client=clients["default_tenant"],
    ),
    "default_hybrid_id_token": LoginSession(
        response_type="code id_token",
        response_mode="fragment",
        redirect_uri="https://nantes.city/callback",
        scope=["openid", "offline_access"],
        state="STATE",
        client=clients["default_tenant"],
    ),
    "default_hybrid_token": LoginSession(
        response_type="code token",
        response_mode="fragment",
        redirect_uri="https://nantes.city/callback",
        scope=["openid", "offline_access"],
        state="STATE",
        client=clients["default_tenant"],
    ),
    "default_hybrid_id_token_token": LoginSession(
        response_type="code id_token token",
        response_mode="fragment",
        redirect_uri="https://nantes.city/callback",
        scope=["openid", "offline_access"],
        state="STATE",
        client=clients["default_tenant"],
    ),
    "granted_default": LoginSession(
        response_type="code",
        response_mode="query",
        redirect_uri="https://nantes.city/callback",
        scope=["openid", "offline_access"],
        state="STATE",
        nonce="NONCE",
        client=clients["granted_default_tenant"],
    ),
    "granted_default_larger_scope": LoginSession(
        response_type="code",
        response_mode="query",
        redirect_uri="https://nantes.city/callback",
        scope=["openid", "offline_access", "other"],
        state="STATE",
        nonce="NONCE",
        client=clients["granted_default_tenant"],
    ),
    "first_party_default": LoginSession(
        response_type="code",
        response_mode="query",
        redirect_uri="https://nantes.city/callback",
        scope=["openid", "offline_access", "other"],
        state="STATE",
        nonce="NONCE",
        client=clients["first_party_default_tenant"],
    ),
    "secondary": LoginSession(
        response_type="code",
        response_mode="query",
        redirect_uri="https://nantes.city/callback",
        scope=["openid", "offline_access"],
        state="STATE",
        nonce="NONCE",
        client=clients["secondary_tenant"],
    ),
}

authorization_code_codes: Mapping[str, Tuple[str, str]] = {
    "default_regular": generate_token(),
    "default_regular_code_challenge_plain": generate_token(),
    "default_regular_code_challenge_s256": generate_token(),
    "default_regular_nonce": generate_token(),
    "secondary_regular": generate_token(),
    "expired": generate_token(),
}

authorization_codes: ModelMapping[AuthorizationCode] = {
    "default_regular": AuthorizationCode(
        code=authorization_code_codes["default_regular"][1],
        c_hash=get_validation_hash(authorization_code_codes["default_regular"][0]),
        redirect_uri="https://bretagne.duchy/callback",
        user=users["regular"],
        client=clients["default_tenant"],
        scope=["openid", "offline_access"],
        authenticated_at=now,
    ),
    "default_regular_code_challenge_plain": AuthorizationCode(
        code=authorization_code_codes["default_regular_code_challenge_plain"][1],
        c_hash=get_validation_hash(
            authorization_code_codes["default_regular_code_challenge_plain"][0]
        ),
        redirect_uri="https://bretagne.duchy/callback",
        user=users["regular"],
        client=clients["default_tenant"],
        scope=["openid", "offline_access"],
        code_challenge="PLAIN_CODE_CHALLENGE",
        code_challenge_method="plain",
        authenticated_at=now,
    ),
    "default_regular_code_challenge_s256": AuthorizationCode(
        code=authorization_code_codes["default_regular_code_challenge_s256"][1],
        c_hash=get_validation_hash(
            authorization_code_codes["default_regular_code_challenge_s256"][0]
        ),
        redirect_uri="https://bretagne.duchy/callback",
        user=users["regular"],
        client=clients["default_tenant"],
        scope=["openid", "offline_access"],
        code_challenge=get_code_verifier_hash("S256_CODE_CHALLENGE"),
        code_challenge_method="S256",
        authenticated_at=now,
    ),
    "default_regular_nonce": AuthorizationCode(
        code=authorization_code_codes["default_regular_nonce"][1],
        c_hash=get_validation_hash(
            authorization_code_codes["default_regular_nonce"][0]
        ),
        redirect_uri="https://bretagne.duchy/callback",
        user=users["regular"],
        client=clients["default_tenant"],
        scope=["openid", "offline_access"],
        nonce="NONCE",
        authenticated_at=now,
    ),
    "secondary_regular": AuthorizationCode(
        code=authorization_code_codes["secondary_regular"][1],
        c_hash=get_validation_hash(authorization_code_codes["secondary_regular"][0]),
        redirect_uri="https://nantes.city/callback",
        user=users["regular_secondary"],
        client=clients["secondary_tenant"],
        scope=["openid"],
        authenticated_at=now,
    ),
    "expired": AuthorizationCode(
        created_at=datetime.now(timezone.utc)
        - timedelta(seconds=settings.authorization_code_lifetime_seconds),
        code=authorization_code_codes["expired"][1],
        c_hash=get_validation_hash(authorization_code_codes["expired"][0]),
        redirect_uri="https://bretagne.duchy/callback",
        user=users["regular"],
        client=clients["default_tenant"],
        scope=["openid", "offline_access"],
        authenticated_at=now,
    ),
}


refresh_token_tokens: Mapping[str, Tuple[str, str]] = {
    "default_regular": generate_token(),
}

refresh_tokens: ModelMapping[RefreshToken] = {
    "default_regular": RefreshToken(
        token=refresh_token_tokens["default_regular"][1],
        expires_at=datetime.now(timezone.utc) + timedelta(seconds=3600),
        user=users["regular"],
        client=clients["default_tenant"],
        scope=["openid", "offline_access"],
        authenticated_at=now,
    )
}


session_token_tokens: Mapping[str, Tuple[str, str]] = {
    "regular": generate_token(),
    "regular_secondary": generate_token(),
}

session_tokens: ModelMapping[SessionToken] = {
    "regular": SessionToken(
        token=session_token_tokens["regular"][1],
        expires_at=datetime.now(timezone.utc) + timedelta(seconds=3600),
        user=users["regular"],
    ),
    "regular_secondary": SessionToken(
        token=session_token_tokens["regular_secondary"][1],
        expires_at=datetime.now(timezone.utc) + timedelta(seconds=3600),
        user=users["regular_secondary"],
    ),
}

grants: ModelMapping[Grant] = {
    "regular_default_granted": Grant(
        scope=["openid", "offline_access"],
        user=users["regular"],
        client=clients["granted_default_tenant"],
    ),
}

data_mapping: TestData = {
    "tenants": tenants,
    "clients": clients,
    "users": users,
    "login_sessions": login_sessions,
    "authorization_codes": authorization_codes,
    "refresh_tokens": refresh_tokens,
    "session_tokens": session_tokens,
    "grants": grants,
}

__all__ = [
    "authorization_code_codes",
    "data_mapping",
    "refresh_token_tokens",
    "session_token_tokens",
    "TestData",
]
