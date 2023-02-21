import secrets
import uuid
from collections.abc import Mapping
from datetime import date, datetime, timedelta, timezone
from typing import TypedDict

from fief.crypto.code_challenge import get_code_verifier_hash
from fief.crypto.id_token import get_validation_hash
from fief.crypto.jwk import generate_jwk
from fief.crypto.password import password_helper
from fief.crypto.token import generate_token
from fief.models import (
    AuthorizationCode,
    Client,
    ClientType,
    EmailTemplate,
    Grant,
    LoginSession,
    M,
    OAuthAccount,
    OAuthProvider,
    OAuthSession,
    Permission,
    RefreshToken,
    RegistrationSession,
    RegistrationSessionFlow,
    Role,
    SessionToken,
    Tenant,
    Theme,
    User,
    UserField,
    UserFieldType,
    UserFieldValue,
    UserPermission,
    UserRole,
)
from fief.services.email_template.types import EmailTemplateType
from fief.services.oauth_provider import AvailableOAuthProvider
from fief.settings import settings

ModelMapping = Mapping[str, M]

now = datetime.now(timezone.utc)
hashed_password = password_helper.hash("hermine")


class TestData(TypedDict):
    __test__ = False

    tenants: ModelMapping[Tenant]
    clients: ModelMapping[Client]
    oauth_providers: ModelMapping[OAuthProvider]
    user_fields: ModelMapping[UserField]
    users: ModelMapping[User]
    user_field_values: ModelMapping[UserFieldValue]
    login_sessions: ModelMapping[LoginSession]
    registration_sessions: ModelMapping[RegistrationSession]
    oauth_sessions: ModelMapping[OAuthSession]
    authorization_codes: ModelMapping[AuthorizationCode]
    refresh_tokens: ModelMapping[RefreshToken]
    session_tokens: ModelMapping[SessionToken]
    oauth_accounts: ModelMapping[OAuthAccount]
    grants: ModelMapping[Grant]
    permissions: ModelMapping[Permission]
    roles: ModelMapping[Role]
    user_permissions: ModelMapping[UserPermission]
    user_roles: ModelMapping[UserRole]
    email_templates: ModelMapping[EmailTemplate]
    themes: ModelMapping[Theme]


oauth_providers: ModelMapping[OAuthProvider] = {
    "google": OAuthProvider(
        provider=AvailableOAuthProvider.GOOGLE,
        scopes=["custom_scope"],
        client_id="GOOGLE_CLIENT_ID",
        client_secret="GOOGLE_CLIENT_SECRET",
    ),
    "openid": OAuthProvider(
        provider=AvailableOAuthProvider.OPENID,
        scopes=["openid"],
        client_id="OPENID_CLIENT_ID",
        client_secret="OPENID_CLIENT_SECRET",
        openid_configuration_endpoint="http://rome.city/.well-known/openid-configuration",
    ),
}

tenants: ModelMapping[Tenant] = {
    "default": Tenant(name="Default", slug="default", default=True, oauth_providers=[]),
    "secondary": Tenant(
        name="Secondary", slug="secondary", default=False, oauth_providers=[]
    ),
    "registration_disabled": Tenant(
        name="Registration disabled",
        slug="registration-disabled",
        default=False,
        registration_allowed=False,
        oauth_providers=[],
    ),
}

client_encryption_key = generate_jwk(secrets.token_urlsafe(), "enc")

clients: ModelMapping[Client] = {
    "default_tenant": Client(
        name="Default",
        tenant=tenants["default"],
        client_id="DEFAULT_TENANT_CLIENT_ID",
        client_secret="DEFAULT_TENANT_CLIENT_SECRET",
        redirect_uris=["https://nantes.city/callback"],
        authorization_code_lifetime_seconds=settings.default_authorization_code_lifetime_seconds,
        access_id_token_lifetime_seconds=settings.default_access_id_token_lifetime_seconds,
        refresh_token_lifetime_seconds=settings.default_refresh_token_lifetime_seconds,
    ),
    "granted_default_tenant": Client(
        name="Granted default",
        tenant=tenants["default"],
        client_id="GRANTED_DEFAULT_TENANT_CLIENT_ID",
        client_secret="GRANTED_DEFAULT_TENANT_CLIENT_SECRET",
        redirect_uris=["https://nantes.city/callback"],
        authorization_code_lifetime_seconds=settings.default_authorization_code_lifetime_seconds,
        access_id_token_lifetime_seconds=settings.default_access_id_token_lifetime_seconds,
        refresh_token_lifetime_seconds=settings.default_refresh_token_lifetime_seconds,
    ),
    "first_party_default_tenant": Client(
        name="First-party default",
        first_party=True,
        tenant=tenants["default"],
        client_id="FIRST_PARTY_DEFAULT_TENANT_CLIENT_ID",
        client_secret="FIRST_PARTY_DEFAULT_TENANT_CLIENT_SECRET",
        redirect_uris=["https://nantes.city/callback"],
        authorization_code_lifetime_seconds=settings.default_authorization_code_lifetime_seconds,
        access_id_token_lifetime_seconds=settings.default_access_id_token_lifetime_seconds,
        refresh_token_lifetime_seconds=settings.default_refresh_token_lifetime_seconds,
    ),
    "public_default_tenant": Client(
        name="Default",
        client_type=ClientType.PUBLIC,
        tenant=tenants["default"],
        client_id="PUBLIC_DEFAULT_TENANT_CLIENT_ID",
        client_secret="PUBLIC_DEFAULT_TENANT_CLIENT_SECRET",
        redirect_uris=["https://nantes.city/callback"],
        authorization_code_lifetime_seconds=settings.default_authorization_code_lifetime_seconds,
        access_id_token_lifetime_seconds=settings.default_access_id_token_lifetime_seconds,
        refresh_token_lifetime_seconds=settings.default_refresh_token_lifetime_seconds,
    ),
    "encryption_default_tenant": Client(
        name="Encryption default",
        tenant=tenants["default"],
        client_id="ENCRYPTION_DEFAULT_TENANT_CLIENT_ID",
        client_secret="ENCRYPTION_DEFAULT_TENANT_CLIENT_SECRET",
        encrypt_jwk=client_encryption_key.export_public(),
        redirect_uris=["https://nantes.city/callback"],
        authorization_code_lifetime_seconds=settings.default_authorization_code_lifetime_seconds,
        access_id_token_lifetime_seconds=settings.default_access_id_token_lifetime_seconds,
        refresh_token_lifetime_seconds=settings.default_refresh_token_lifetime_seconds,
    ),
    "secondary_tenant": Client(
        name="Secondary",
        tenant=tenants["secondary"],
        redirect_uris=["https://nantes.city/callback"],
        authorization_code_lifetime_seconds=settings.default_authorization_code_lifetime_seconds,
        access_id_token_lifetime_seconds=settings.default_access_id_token_lifetime_seconds,
        refresh_token_lifetime_seconds=settings.default_refresh_token_lifetime_seconds,
    ),
    "registration_disabled_tenant": Client(
        name="Registration disabled",
        tenant=tenants["registration_disabled"],
        redirect_uris=["https://nantes.city/callback"],
        authorization_code_lifetime_seconds=settings.default_authorization_code_lifetime_seconds,
        access_id_token_lifetime_seconds=settings.default_access_id_token_lifetime_seconds,
        refresh_token_lifetime_seconds=settings.default_refresh_token_lifetime_seconds,
    ),
}

user_fields: ModelMapping[UserField] = {
    "given_name": UserField(
        name="Given name",
        slug="given_name",
        type=UserFieldType.STRING,
        configuration={
            "choices": None,
            "default": None,
            "at_registration": True,
            "at_update": True,
            "required": False,
        },
    ),
    "gender": UserField(
        name="Gender",
        slug="gender",
        type=UserFieldType.CHOICE,
        configuration={
            "choices": [("M", "male"), ("F", "female"), ("N", "non_binary")],
            "default": None,
            "at_registration": False,
            "at_update": True,
            "required": False,
        },
    ),
    "phone_number": UserField(
        name="Phone number",
        slug="phone_number",
        type=UserFieldType.PHONE_NUMBER,
        configuration={
            "choices": None,
            "default": None,
            "at_registration": False,
            "at_update": True,
            "required": False,
        },
    ),
    "phone_number_verified": UserField(
        name="Phone number verified",
        slug="phone_number_verified",
        type=UserFieldType.BOOLEAN,
        configuration={
            "choices": None,
            "default": None,
            "at_registration": False,
            "at_update": False,
            "required": False,
        },
    ),
    "birthdate": UserField(
        name="Birthdate",
        slug="birthdate",
        type=UserFieldType.DATE,
        configuration={
            "choices": None,
            "default": None,
            "at_registration": False,
            "at_update": True,
            "required": False,
        },
    ),
    "last_seen": UserField(
        name="Last seen",
        slug="last_seen",
        type=UserFieldType.DATETIME,
        configuration={
            "choices": None,
            "default": None,
            "at_registration": False,
            "at_update": False,
            "required": False,
        },
    ),
    "address": UserField(
        name="Address",
        slug="address",
        type=UserFieldType.ADDRESS,
        configuration={
            "choices": None,
            "default": None,
            "at_registration": True,
            "at_update": False,
            "required": False,
        },
    ),
    "onboarding_done": UserField(
        name="Onboarding done",
        slug="onboarding_done",
        type=UserFieldType.BOOLEAN,
        configuration={
            "choices": None,
            "default": False,
            "at_registration": False,
            "at_update": False,
            "required": False,
        },
    ),
}

users: ModelMapping[User] = {
    "regular": User(
        id=uuid.uuid4(),
        created_at=datetime.now(tz=timezone.utc),
        email="anne@bretagne.duchy",
        hashed_password=hashed_password,
        tenant=tenants["default"],
    ),
    "regular_secondary": User(
        id=uuid.uuid4(),
        created_at=datetime.now(tz=timezone.utc) + timedelta(seconds=1),
        email="anne@nantes.city",
        hashed_password=hashed_password,
        tenant=tenants["secondary"],
    ),
    "regular_default_2": User(
        id=uuid.uuid4(),
        created_at=datetime.now(tz=timezone.utc) + timedelta(seconds=2),
        email="isabeau@bretagne.duchy",
        hashed_password=hashed_password,
        tenant=tenants["default"],
    ),
    "inactive": User(
        id=uuid.uuid4(),
        created_at=datetime.now(tz=timezone.utc) + timedelta(seconds=3),
        email="marguerite@bretagne.duchy",
        hashed_password=hashed_password,
        is_active=False,
        tenant=tenants["default"],
    ),
}

user_field_values: ModelMapping[UserFieldValue] = {
    "regular_given_name": UserFieldValue(
        value_string="Anne",
        user=users["regular"],
        user_field=user_fields["given_name"],
    ),
    "regular_gender": UserFieldValue(
        value_string="F",
        user=users["regular"],
        user_field=user_fields["gender"],
    ),
    "regular_phone_number": UserFieldValue(
        value_string="+33642424242",
        user=users["regular"],
        user_field=user_fields["phone_number"],
    ),
    "regular_phone_number_verified": UserFieldValue(
        value_boolean=True,
        user=users["regular"],
        user_field=user_fields["phone_number_verified"],
    ),
    "regular_birthdate": UserFieldValue(
        value_date=date(1477, 1, 25),
        user=users["regular"],
        user_field=user_fields["birthdate"],
    ),
    "regular_last_seen": UserFieldValue(
        value_datetime=datetime(2022, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
        user=users["regular"],
        user_field=user_fields["last_seen"],
    ),
    "regular_address": UserFieldValue(
        value_json={
            "line1": "4 place Marc Elder",
            "postal_code": "44000",
            "city": "Nantes",
            "country": "FR",
        },
        user=users["regular"],
        user_field=user_fields["address"],
    ),
    "regular_onboarding_done": UserFieldValue(
        value_boolean=False,
        user=users["regular"],
        user_field=user_fields["onboarding_done"],
    ),
    "secondary_regular_given_name": UserFieldValue(
        value_string="Anne",
        user=users["regular_secondary"],
        user_field=user_fields["given_name"],
    ),
    "secondary_onboarding_done": UserFieldValue(
        value_boolean=False,
        user=users["regular_secondary"],
        user_field=user_fields["onboarding_done"],
    ),
}

oauth_accounts: ModelMapping[OAuthAccount] = {
    "regular_google": OAuthAccount(
        access_token="REGULAR_GOOGLE_ACCESS_TOKEN",
        expires_at=datetime.now(timezone.utc) + timedelta(seconds=3600),
        refresh_token="REGULAR_GOOGLE_REFRESH_TOKEN",
        account_id="REGULAR_GOOGLE_ACCOUNT_ID",
        account_email="anne@bretagne.duchy",
        oauth_provider=oauth_providers["google"],
        user=users["regular"],
        tenant=tenants["default"],
    ),
    "regular_openid_expired": OAuthAccount(
        access_token="REGULAR_OPENID_ACCESS_TOKEN",
        expires_at=datetime.now(timezone.utc) - timedelta(seconds=3600),
        refresh_token="REGULAR_OPENID_REFRESH_TOKEN",
        account_id="REGULAR_OPENID_ACCOUNT_ID",
        account_email="anne@bretagne.duchy",
        oauth_provider=oauth_providers["openid"],
        user=users["regular"],
        tenant=tenants["default"],
    ),
    "inactive_google": OAuthAccount(
        access_token="INACTIVE_GOOGLE_ACCESS_TOKEN",
        expires_at=datetime.now(timezone.utc) + timedelta(seconds=3600),
        refresh_token="INACTIVE_GOOGLE_REFRESH_TOKEN",
        account_id="INACTIVE_GOOGLE_ACCOUNT_ID",
        account_email="marguerite@bretagne.duchy",
        oauth_provider=oauth_providers["google"],
        user=users["inactive"],
        tenant=tenants["default"],
    ),
    "new_user_google": OAuthAccount(
        access_token="NEW_USER_GOOGLE_ACCESS_TOKEN",
        expires_at=datetime.now(timezone.utc) + timedelta(seconds=3600),
        refresh_token="NEW_USER_GOOGLE_REFRESH_TOKEN",
        account_id="NEW_USER_GOOGLE_ACCOUNT_ID",
        account_email="louis@bretagne.duchy",
        oauth_provider=oauth_providers["google"],
        tenant=tenants["default"],
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
    "registration_disabled": LoginSession(
        response_type="code",
        response_mode="query",
        redirect_uri="https://nantes.city/callback",
        scope=["openid", "offline_access"],
        state="STATE",
        nonce="NONCE",
        client=clients["registration_disabled_tenant"],
    ),
}

registration_sessions: ModelMapping[RegistrationSession] = {
    "default_password": RegistrationSession(
        flow=RegistrationSessionFlow.PASSWORD,
        tenant=tenants["default"],
    ),
    "secondary_password": RegistrationSession(
        flow=RegistrationSessionFlow.PASSWORD,
        tenant=tenants["secondary"],
    ),
    "default_oauth": RegistrationSession(
        flow=RegistrationSessionFlow.OAUTH,
        email="louis@bretagne.duchy",
        oauth_account=oauth_accounts["new_user_google"],
        tenant=tenants["default"],
    ),
    "secondary_oauth": RegistrationSession(
        flow=RegistrationSessionFlow.OAUTH,
        email="louis@nantes.city",
        oauth_account=oauth_accounts["new_user_google"],
        tenant=tenants["secondary"],
    ),
}

oauth_sessions: ModelMapping[OAuthSession] = {
    "default_google": OAuthSession(
        redirect_uri="http://api.fief.dev/oauth/callback",
        oauth_provider=oauth_providers["google"],
        login_session=login_sessions["default"],
        tenant=tenants["default"],
    ),
}

authorization_code_codes: Mapping[str, tuple[str, str]] = {
    "default_regular": generate_token(),
    "default_regular_code_challenge_plain": generate_token(),
    "default_regular_code_challenge_s256": generate_token(),
    "default_regular_nonce": generate_token(),
    "secondary_regular": generate_token(),
    "expired": generate_token(),
    "default_public_regular_no_code_challenge": generate_token(),
    "default_public_regular_code_challenge_s256": generate_token(),
    "default_id_token_encryption": generate_token(),
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
        expires_at=clients["default_tenant"].get_authorization_code_expires_at(),
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
        expires_at=clients["default_tenant"].get_authorization_code_expires_at(),
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
        expires_at=clients["default_tenant"].get_authorization_code_expires_at(),
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
        expires_at=clients["default_tenant"].get_authorization_code_expires_at(),
    ),
    "secondary_regular": AuthorizationCode(
        code=authorization_code_codes["secondary_regular"][1],
        c_hash=get_validation_hash(authorization_code_codes["secondary_regular"][0]),
        redirect_uri="https://nantes.city/callback",
        user=users["regular_secondary"],
        client=clients["secondary_tenant"],
        scope=["openid"],
        authenticated_at=now,
        expires_at=clients["secondary_tenant"].get_authorization_code_expires_at(),
    ),
    "expired": AuthorizationCode(
        expires_at=datetime.now(timezone.utc)
        - timedelta(
            seconds=clients["default_tenant"].authorization_code_lifetime_seconds
        ),
        code=authorization_code_codes["expired"][1],
        c_hash=get_validation_hash(authorization_code_codes["expired"][0]),
        redirect_uri="https://bretagne.duchy/callback",
        user=users["regular"],
        client=clients["default_tenant"],
        scope=["openid", "offline_access"],
        authenticated_at=now,
    ),
    "default_public_regular_no_code_challenge": AuthorizationCode(
        code=authorization_code_codes["default_public_regular_no_code_challenge"][1],
        c_hash=get_validation_hash(
            authorization_code_codes["default_public_regular_no_code_challenge"][0]
        ),
        redirect_uri="https://bretagne.duchy/callback",
        user=users["regular"],
        client=clients["public_default_tenant"],
        scope=["openid", "offline_access"],
        authenticated_at=now,
        expires_at=clients["public_default_tenant"].get_authorization_code_expires_at(),
    ),
    "default_public_regular_code_challenge_s256": AuthorizationCode(
        code=authorization_code_codes["default_public_regular_code_challenge_s256"][1],
        c_hash=get_validation_hash(
            authorization_code_codes["default_public_regular_code_challenge_s256"][0]
        ),
        redirect_uri="https://bretagne.duchy/callback",
        user=users["regular"],
        client=clients["public_default_tenant"],
        scope=["openid", "offline_access"],
        code_challenge=get_code_verifier_hash("S256_CODE_CHALLENGE"),
        code_challenge_method="S256",
        authenticated_at=now,
        expires_at=clients["public_default_tenant"].get_authorization_code_expires_at(),
    ),
    "default_id_token_encryption": AuthorizationCode(
        code=authorization_code_codes["default_id_token_encryption"][1],
        c_hash=get_validation_hash(
            authorization_code_codes["default_id_token_encryption"][0]
        ),
        redirect_uri="https://bretagne.duchy/callback",
        user=users["regular"],
        client=clients["encryption_default_tenant"],
        scope=["openid", "offline_access"],
        authenticated_at=now,
        expires_at=clients[
            "encryption_default_tenant"
        ].get_authorization_code_expires_at(),
    ),
}

refresh_token_tokens: Mapping[str, tuple[str, str]] = {
    "default_regular": generate_token(),
    "default_public_regular": generate_token(),
}

refresh_tokens: ModelMapping[RefreshToken] = {
    "default_regular": RefreshToken(
        token=refresh_token_tokens["default_regular"][1],
        user=users["regular"],
        client=clients["default_tenant"],
        scope=["openid", "offline_access"],
        authenticated_at=now,
        expires_at=clients["default_tenant"].get_refresh_token_expires_at(),
    ),
    "default_public_regular": RefreshToken(
        token=refresh_token_tokens["default_public_regular"][1],
        user=users["regular"],
        client=clients["public_default_tenant"],
        scope=["openid", "offline_access"],
        authenticated_at=now,
        expires_at=clients["default_tenant"].get_refresh_token_expires_at(),
    ),
}

session_token_tokens: Mapping[str, tuple[str, str]] = {
    "regular": generate_token(),
    "regular_secondary": generate_token(),
}

session_tokens: ModelMapping[SessionToken] = {
    "regular": SessionToken(
        token=session_token_tokens["regular"][1],
        user=users["regular"],
    ),
    "regular_secondary": SessionToken(
        token=session_token_tokens["regular_secondary"][1],
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

permissions: ModelMapping[Permission] = {
    "castles:create": Permission(
        name="Create Castles",
        codename="castles:create",
    ),
    "castles:read": Permission(
        name="Read Castles",
        codename="castles:read",
    ),
    "castles:update": Permission(
        name="Update Castles",
        codename="castles:update",
    ),
    "castles:delete": Permission(
        name="Delete Castles",
        codename="castles:delete",
    ),
}

roles: ModelMapping[Role] = {
    "castles_visitor": Role(
        name="Castles Visitor",
        granted_by_default=True,
        permissions=[permissions["castles:read"]],
    ),
    "castles_manager": Role(
        name="Castles Manager",
        granted_by_default=False,
        permissions=[
            permissions["castles:read"],
            permissions["castles:create"],
            permissions["castles:update"],
            permissions["castles:delete"],
        ],
    ),
}

user_permissions: ModelMapping[UserPermission] = {
    "default_castles_visitor_from_role": UserPermission(
        user=users["regular"],
        permission=permissions["castles:read"],
        from_role=roles["castles_visitor"],
    ),
    "default_castles_delete_direct": UserPermission(
        user=users["regular"],
        permission=permissions["castles:delete"],
    ),
}

user_roles: ModelMapping[UserRole] = {
    "default_castles_visitor": UserRole(
        user=users["regular"],
        role=roles["castles_visitor"],
    ),
}

email_templates: ModelMapping[EmailTemplate] = {
    "base": EmailTemplate(
        type=EmailTemplateType.BASE,
        subject="",
        content="<html><body><h1>{{ tenant.name }}</h1>{% block main %}{% endblock %}</body></html>",
    ),
    "welcome": EmailTemplate(
        type=EmailTemplateType.WELCOME,
        subject="TITLE",
        content='{% extends "BASE" %}{% block main %}WELCOME{% endblock %}',
    ),
    "forgot_password": EmailTemplate(
        type=EmailTemplateType.FORGOT_PASSWORD,
        subject="TITLE",
        content='{% extends "BASE" %}{% block main %}FORGOT_PASSWORD {{ reset_url }}{% endblock %}',
    ),
}

themes: ModelMapping[Theme] = {
    "default": Theme.build_default(),
    "custom": Theme(
        name="Default",
        default=False,
        primary_color="#f43f5e",
        primary_color_hover="#e11d48",
        primary_color_light="#fda4af",
        input_color="#1e293b",
        input_color_background="#ffffff",
        light_color="#e2e8f0",
        light_color_hover="#cbd5e1",
        text_color="#475569",
        accent_color="#1e293b",
        background_color="#ffffff",
        font_size=16,
        font_family="'Inter', sans-serif",
    ),
}

data_mapping: TestData = {
    "tenants": tenants,
    "clients": clients,
    "oauth_providers": oauth_providers,
    "user_fields": user_fields,
    "users": users,
    "user_field_values": user_field_values,
    "login_sessions": login_sessions,
    "registration_sessions": registration_sessions,
    "oauth_sessions": oauth_sessions,
    "authorization_codes": authorization_codes,
    "refresh_tokens": refresh_tokens,
    "session_tokens": session_tokens,
    "oauth_accounts": oauth_accounts,
    "grants": grants,
    "permissions": permissions,
    "roles": roles,
    "user_permissions": user_permissions,
    "user_roles": user_roles,
    "email_templates": email_templates,
    "themes": themes,
}

__all__ = [
    "authorization_code_codes",
    "data_mapping",
    "refresh_token_tokens",
    "session_token_tokens",
    "TestData",
]
