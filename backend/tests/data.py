import secrets
import uuid
from datetime import datetime, timedelta, timezone, tzinfo
from typing import Mapping, TypedDict

from fief.crypto.jwk import generate_jwk
from fief.crypto.password import password_helper
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
    ),
    "granted_default_tenant": Client(
        name="Granted default",
        tenant=tenants["default"],
        client_id="GRANTED_DEFAULT_TENANT_CLIENT_ID",
        client_secret="GRANTED_DEFAULT_TENANT_CLIENT_SECRET",
    ),
    "first_party_default_tenant": Client(
        name="First-party default",
        first_party=True,
        tenant=tenants["default"],
        client_id="FIRST_PARTY_DEFAULT_TENANT_CLIENT_ID",
        client_secret="FIRST_PARTY_DEFAULT_TENANT_CLIENT_SECRET",
    ),
    "encryption_default_tenant": Client(
        name="Encryption default",
        tenant=tenants["default"],
        client_id="ENCRYPTION_DEFAULT_TENANT_CLIENT_ID",
        client_secret="ENCRYPTION_DEFAULT_TENANT_CLIENT_SECRET",
        encrypt_jwk=generate_jwk(secrets.token_urlsafe(), "enc").export_public(),
    ),
    "secondary_tenant": Client(name="Secondary", tenant=tenants["secondary"]),
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
        redirect_uri="https://nantes.city/callback",
        scope=["openid", "offline_access"],
        state="STATE",
        nonce="NONCE",
        client=clients["default_tenant"],
    ),
    "default_none_prompt": LoginSession(
        response_type="code",
        redirect_uri="https://nantes.city/callback",
        scope=["openid", "offline_access"],
        state="STATE",
        nonce="NONCE",
        client=clients["default_tenant"],
        prompt="none",
    ),
    "granted_default": LoginSession(
        response_type="code",
        redirect_uri="https://nantes.city/callback",
        scope=["openid", "offline_access"],
        state="STATE",
        nonce="NONCE",
        client=clients["granted_default_tenant"],
    ),
    "granted_default_larger_scope": LoginSession(
        response_type="code",
        redirect_uri="https://nantes.city/callback",
        scope=["openid", "offline_access", "other"],
        state="STATE",
        nonce="NONCE",
        client=clients["granted_default_tenant"],
    ),
    "first_party_default": LoginSession(
        response_type="code",
        redirect_uri="https://nantes.city/callback",
        scope=["openid", "offline_access", "other"],
        state="STATE",
        nonce="NONCE",
        client=clients["first_party_default_tenant"],
    ),
    "secondary": LoginSession(
        response_type="code",
        redirect_uri="https://nantes.city/callback",
        scope=["openid", "offline_access"],
        state="STATE",
        nonce="NONCE",
        client=clients["secondary_tenant"],
    ),
}

authorization_codes: ModelMapping[AuthorizationCode] = {
    "default_regular": AuthorizationCode(
        redirect_uri="https://bretagne.duchy/callback",
        user=users["regular"],
        client=clients["default_tenant"],
        scope=["openid", "offline_access"],
    ),
    "default_regular_nonce": AuthorizationCode(
        redirect_uri="https://bretagne.duchy/callback",
        user=users["regular"],
        client=clients["default_tenant"],
        scope=["openid", "offline_access"],
        nonce="NONCE",
    ),
    "secondary_regular": AuthorizationCode(
        redirect_uri="https://nantes.city/callback",
        user=users["regular_secondary"],
        client=clients["secondary_tenant"],
        scope=["openid"],
    ),
    "expired": AuthorizationCode(
        created_at=datetime.now(timezone.utc)
        - timedelta(seconds=settings.authorization_code_lifetime_seconds),
        redirect_uri="https://bretagne.duchy/callback",
        user=users["regular"],
        client=clients["default_tenant"],
        scope=["openid", "offline_access"],
    ),
}

refresh_tokens: ModelMapping[RefreshToken] = {
    "default_regular": RefreshToken(
        expires_at=datetime.now(timezone.utc) + timedelta(seconds=3600),
        user=users["regular"],
        client=clients["default_tenant"],
        scope=["openid", "offline_access"],
    )
}

session_tokens: ModelMapping[SessionToken] = {
    "regular": SessionToken(
        expires_at=datetime.now(timezone.utc) + timedelta(seconds=3600),
        user=users["regular"],
    ),
    "regular_secondary": SessionToken(
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

__all__ = ["data_mapping", "TestData"]
