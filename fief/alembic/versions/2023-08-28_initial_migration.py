"""Initial migration

Revision ID: 6c06c7d908a7
Revises:
Create Date: 2023-08-28 17:05:23.479609

"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

import fief

# revision identifiers, used by Alembic.
revision = "6c06c7d908a7"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    table_prefix = op.get_context().opts["table_prefix"]

    connection = op.get_bind()
    dialect = connection.dialect.name

    op.create_table(
        f"{table_prefix}audit_logs",
        sa.Column(
            "timestamp",
            fief.models.generics.TIMESTAMPAware(timezone=True),
            nullable=False,
        ),
        sa.Column("level", sa.String(length=255), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("extra", sa.JSON(), nullable=True),
        sa.Column("subject_user_id", fief.models.generics.GUID(), nullable=True),
        sa.Column("object_id", fief.models.generics.GUID(), nullable=True),
        sa.Column("object_class", sa.String(length=255), nullable=True),
        sa.Column("admin_user_id", fief.models.generics.GUID(), nullable=True),
        sa.Column("admin_api_key_id", fief.models.generics.GUID(), nullable=True),
        sa.Column("id", fief.models.generics.GUID(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f(f"ix_{table_prefix}audit_logs_admin_api_key_id"),
        f"{table_prefix}audit_logs",
        ["admin_api_key_id"],
        unique=False,
    )
    op.create_index(
        op.f(f"ix_{table_prefix}audit_logs_admin_user_id"),
        f"{table_prefix}audit_logs",
        ["admin_user_id"],
        unique=False,
    )
    op.create_index(
        op.f(f"ix_{table_prefix}audit_logs_level"),
        f"{table_prefix}audit_logs",
        ["level"],
        unique=False,
    )
    op.create_index(
        op.f(f"ix_{table_prefix}audit_logs_object_class"),
        f"{table_prefix}audit_logs",
        ["object_class"],
        unique=False,
    )
    op.create_index(
        op.f(f"ix_{table_prefix}audit_logs_object_id"),
        f"{table_prefix}audit_logs",
        ["object_id"],
        unique=False,
    )
    op.create_index(
        op.f(f"ix_{table_prefix}audit_logs_subject_user_id"),
        f"{table_prefix}audit_logs",
        ["subject_user_id"],
        unique=False,
    )
    op.create_index(
        op.f(f"ix_{table_prefix}audit_logs_timestamp"),
        f"{table_prefix}audit_logs",
        ["timestamp"],
        unique=False,
    )
    op.create_table(
        f"{table_prefix}email_domains",
        sa.Column("email_provider", sa.String(length=255), nullable=False),
        sa.Column("domain_id", sa.String(length=255), nullable=False),
        sa.Column("domain", sa.String(length=255), nullable=False),
        sa.Column("records", sa.JSON(), nullable=False),
        sa.Column("id", fief.models.generics.GUID(), nullable=False),
        sa.Column(
            "created_at",
            fief.models.generics.TIMESTAMPAware(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            fief.models.generics.TIMESTAMPAware(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("domain"),
    )
    op.create_index(
        op.f(f"ix_{table_prefix}email_domains_created_at"),
        f"{table_prefix}email_domains",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        op.f(f"ix_{table_prefix}email_domains_updated_at"),
        f"{table_prefix}email_domains",
        ["updated_at"],
        unique=False,
    )
    op.create_table(
        f"{table_prefix}email_templates",
        sa.Column("type", sa.String(length=255), nullable=False),
        sa.Column("subject", sa.Text(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("id", fief.models.generics.GUID(), nullable=False),
        sa.Column(
            "created_at",
            fief.models.generics.TIMESTAMPAware(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            fief.models.generics.TIMESTAMPAware(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("type"),
    )
    op.create_index(
        op.f(f"ix_{table_prefix}email_templates_created_at"),
        f"{table_prefix}email_templates",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        op.f(f"ix_{table_prefix}email_templates_updated_at"),
        f"{table_prefix}email_templates",
        ["updated_at"],
        unique=False,
    )
    op.create_table(
        f"{table_prefix}oauth_providers",
        sa.Column("provider", sa.String(length=255), nullable=False),
        sa.Column(
            "client_id", fief.crypto.encryption.StringEncryptedType(), nullable=False
        ),
        sa.Column(
            "client_secret",
            fief.crypto.encryption.StringEncryptedType(),
            nullable=False,
        ),
        sa.Column("scopes", sa.JSON(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=True),
        sa.Column("openid_configuration_endpoint", sa.Text(), nullable=True),
        sa.Column("id", fief.models.generics.GUID(), nullable=False),
        sa.Column(
            "created_at",
            fief.models.generics.TIMESTAMPAware(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            fief.models.generics.TIMESTAMPAware(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f(f"ix_{table_prefix}oauth_providers_created_at"),
        f"{table_prefix}oauth_providers",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        op.f(f"ix_{table_prefix}oauth_providers_updated_at"),
        f"{table_prefix}oauth_providers",
        ["updated_at"],
        unique=False,
    )
    op.create_table(
        f"{table_prefix}permissions",
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("codename", sa.String(length=255), nullable=False),
        sa.Column("id", fief.models.generics.GUID(), nullable=False),
        sa.Column(
            "created_at",
            fief.models.generics.TIMESTAMPAware(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            fief.models.generics.TIMESTAMPAware(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("codename"),
    )
    op.create_index(
        op.f(f"ix_{table_prefix}permissions_created_at"),
        f"{table_prefix}permissions",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        op.f(f"ix_{table_prefix}permissions_updated_at"),
        f"{table_prefix}permissions",
        ["updated_at"],
        unique=False,
    )
    op.create_table(
        f"{table_prefix}roles",
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("granted_by_default", sa.Boolean(), nullable=False),
        sa.Column("id", fief.models.generics.GUID(), nullable=False),
        sa.Column(
            "created_at",
            fief.models.generics.TIMESTAMPAware(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            fief.models.generics.TIMESTAMPAware(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f(f"ix_{table_prefix}roles_created_at"),
        f"{table_prefix}roles",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        op.f(f"ix_{table_prefix}roles_updated_at"),
        f"{table_prefix}roles",
        ["updated_at"],
        unique=False,
    )
    op.create_table(
        f"{table_prefix}themes",
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("default", sa.Boolean(), nullable=False),
        sa.Column("primary_color", sa.String(length=255), nullable=False),
        sa.Column("primary_color_hover", sa.String(length=255), nullable=False),
        sa.Column("primary_color_light", sa.String(length=255), nullable=False),
        sa.Column("input_color", sa.String(length=255), nullable=False),
        sa.Column("input_color_background", sa.String(length=255), nullable=False),
        sa.Column("light_color", sa.String(length=255), nullable=False),
        sa.Column("light_color_hover", sa.String(length=255), nullable=False),
        sa.Column("text_color", sa.String(length=255), nullable=False),
        sa.Column("accent_color", sa.String(length=255), nullable=False),
        sa.Column("background_color", sa.String(length=255), nullable=False),
        sa.Column("font_size", sa.Integer(), nullable=False),
        sa.Column("font_family", sa.String(length=255), nullable=False),
        sa.Column("font_css_url", sa.String(length=512), nullable=True),
        sa.Column("id", fief.models.generics.GUID(), nullable=False),
        sa.Column(
            "created_at",
            fief.models.generics.TIMESTAMPAware(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            fief.models.generics.TIMESTAMPAware(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f(f"ix_{table_prefix}themes_created_at"),
        f"{table_prefix}themes",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        op.f(f"ix_{table_prefix}themes_updated_at"),
        f"{table_prefix}themes",
        ["updated_at"],
        unique=False,
    )

    if dialect == "postgresql":
        user_fields_type_enum = postgresql.ENUM(
            "STRING",
            "INTEGER",
            "BOOLEAN",
            "DATE",
            "DATETIME",
            "CHOICE",
            "PHONE_NUMBER",
            "ADDRESS",
            "TIMEZONE",
            name=f"{table_prefix}userfieldtype",
            create_type=False,
        )
        user_fields_type_enum.create(connection, checkfirst=True)
    else:
        user_fields_type_enum = sa.Enum(
            "STRING",
            "INTEGER",
            "BOOLEAN",
            "DATE",
            "DATETIME",
            "CHOICE",
            "PHONE_NUMBER",
            "ADDRESS",
            "TIMEZONE",
            name=f"{table_prefix}userfieldtype",
        )

    op.create_table(
        f"{table_prefix}user_fields",
        sa.Column("name", sa.String(length=320), nullable=False),
        sa.Column("slug", sa.String(length=320), nullable=False),
        sa.Column(
            "type",
            user_fields_type_enum,
            nullable=True,
        ),
        sa.Column("configuration", sa.JSON(), nullable=False),
        sa.Column("id", fief.models.generics.GUID(), nullable=False),
        sa.Column(
            "created_at",
            fief.models.generics.TIMESTAMPAware(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            fief.models.generics.TIMESTAMPAware(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f(f"ix_{table_prefix}user_fields_created_at"),
        f"{table_prefix}user_fields",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        op.f(f"ix_{table_prefix}user_fields_slug"),
        f"{table_prefix}user_fields",
        ["slug"],
        unique=True,
    )
    op.create_index(
        op.f(f"ix_{table_prefix}user_fields_type"),
        f"{table_prefix}user_fields",
        ["type"],
        unique=False,
    )
    op.create_index(
        op.f(f"ix_{table_prefix}user_fields_updated_at"),
        f"{table_prefix}user_fields",
        ["updated_at"],
        unique=False,
    )
    op.create_table(
        f"{table_prefix}webhooks",
        sa.Column("url", sa.String(length=255), nullable=False),
        sa.Column("secret", sa.String(length=255), nullable=False),
        sa.Column("events", sa.JSON(), nullable=False),
        sa.Column("id", fief.models.generics.GUID(), nullable=False),
        sa.Column(
            "created_at",
            fief.models.generics.TIMESTAMPAware(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            fief.models.generics.TIMESTAMPAware(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f(f"ix_{table_prefix}webhooks_created_at"),
        f"{table_prefix}webhooks",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        op.f(f"ix_{table_prefix}webhooks_updated_at"),
        f"{table_prefix}webhooks",
        ["updated_at"],
        unique=False,
    )
    op.create_table(
        f"{table_prefix}roles_permissions",
        sa.Column("role_id", fief.models.generics.GUID(), nullable=False),
        sa.Column("permission_id", fief.models.generics.GUID(), nullable=False),
        sa.ForeignKeyConstraint(
            ["permission_id"], [f"{table_prefix}permissions.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["role_id"], [f"{table_prefix}roles.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("role_id", "permission_id"),
    )
    op.create_table(
        f"{table_prefix}tenants",
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=False),
        sa.Column("default", sa.Boolean(), nullable=False),
        sa.Column("sign_jwk", sa.Text(), nullable=False),
        sa.Column("registration_allowed", sa.Boolean(), nullable=False),
        sa.Column("application_url", sa.String(length=512), nullable=True),
        sa.Column("theme_id", fief.models.generics.GUID(), nullable=True),
        sa.Column("logo_url", sa.String(length=512), nullable=True),
        sa.Column("email_from_email", sa.String(length=255), nullable=True),
        sa.Column("email_from_name", sa.String(length=255), nullable=True),
        sa.Column("email_domain_id", fief.models.generics.GUID(), nullable=True),
        sa.Column("id", fief.models.generics.GUID(), nullable=False),
        sa.Column(
            "created_at",
            fief.models.generics.TIMESTAMPAware(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            fief.models.generics.TIMESTAMPAware(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["email_domain_id"],
            [f"{table_prefix}email_domains.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["theme_id"], [f"{table_prefix}themes.id"], ondelete="SET NULL"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index(
        op.f(f"ix_{table_prefix}tenants_created_at"),
        f"{table_prefix}tenants",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        op.f(f"ix_{table_prefix}tenants_updated_at"),
        f"{table_prefix}tenants",
        ["updated_at"],
        unique=False,
    )
    op.create_table(
        f"{table_prefix}webhook_logs",
        sa.Column("webhook_id", fief.models.generics.GUID(), nullable=False),
        sa.Column("event", sa.String(length=255), nullable=False),
        sa.Column("attempt", sa.Integer(), nullable=False),
        sa.Column("payload", sa.Text(), nullable=False),
        sa.Column("success", sa.Boolean(), nullable=False),
        sa.Column("response", sa.Text(), nullable=True),
        sa.Column("error_type", sa.String(length=255), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("id", fief.models.generics.GUID(), nullable=False),
        sa.Column(
            "created_at",
            fief.models.generics.TIMESTAMPAware(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            fief.models.generics.TIMESTAMPAware(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["webhook_id"], [f"{table_prefix}webhooks.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f(f"ix_{table_prefix}webhook_logs_created_at"),
        f"{table_prefix}webhook_logs",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        op.f(f"ix_{table_prefix}webhook_logs_updated_at"),
        f"{table_prefix}webhook_logs",
        ["updated_at"],
        unique=False,
    )

    if dialect == "postgresql":
        client_type_enum = postgresql.ENUM(
            "public",
            "confidential",
            name=f"{table_prefix}clienttype",
            create_type=False,
        )
        client_type_enum.create(connection, checkfirst=True)
    else:
        client_type_enum = sa.Enum(
            "public", "confidential", name=f"{table_prefix}clienttype"
        )

    op.create_table(
        f"{table_prefix}clients",
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("first_party", sa.Boolean(), nullable=False),
        sa.Column(
            "client_type",
            client_type_enum,
            server_default="confidential",
            nullable=False,
        ),
        sa.Column("client_id", sa.String(length=255), nullable=False),
        sa.Column("client_secret", sa.String(length=255), nullable=False),
        sa.Column("redirect_uris", sa.JSON(), nullable=False),
        sa.Column("encrypt_jwk", sa.Text(), nullable=True),
        sa.Column("authorization_code_lifetime_seconds", sa.Integer(), nullable=False),
        sa.Column("access_id_token_lifetime_seconds", sa.Integer(), nullable=False),
        sa.Column("refresh_token_lifetime_seconds", sa.Integer(), nullable=False),
        sa.Column("tenant_id", fief.models.generics.GUID(), nullable=False),
        sa.Column("id", fief.models.generics.GUID(), nullable=False),
        sa.Column(
            "created_at",
            fief.models.generics.TIMESTAMPAware(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            fief.models.generics.TIMESTAMPAware(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"], [f"{table_prefix}tenants.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f(f"ix_{table_prefix}clients_client_id"),
        f"{table_prefix}clients",
        ["client_id"],
        unique=False,
    )
    op.create_index(
        op.f(f"ix_{table_prefix}clients_client_secret"),
        f"{table_prefix}clients",
        ["client_secret"],
        unique=False,
    )
    op.create_index(
        op.f(f"ix_{table_prefix}clients_created_at"),
        f"{table_prefix}clients",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        op.f(f"ix_{table_prefix}clients_updated_at"),
        f"{table_prefix}clients",
        ["updated_at"],
        unique=False,
    )
    op.create_table(
        f"{table_prefix}tenants_oauth_providers",
        sa.Column("tenant_id", fief.models.generics.GUID(), nullable=False),
        sa.Column("oauth_provider_id", fief.models.generics.GUID(), nullable=False),
        sa.ForeignKeyConstraint(
            ["oauth_provider_id"],
            [f"{table_prefix}oauth_providers.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"], [f"{table_prefix}tenants.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("tenant_id", "oauth_provider_id"),
    )
    op.create_table(
        f"{table_prefix}users",
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("email_lower", sa.String(length=320), nullable=False),
        sa.Column("email_verified", sa.Boolean(), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("tenant_id", fief.models.generics.GUID(), nullable=False),
        sa.Column("id", fief.models.generics.GUID(), nullable=False),
        sa.Column(
            "created_at",
            fief.models.generics.TIMESTAMPAware(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            fief.models.generics.TIMESTAMPAware(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"], [f"{table_prefix}tenants.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email", "tenant_id"),
    )
    op.create_index(
        op.f(f"ix_{table_prefix}users_created_at"),
        f"{table_prefix}users",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        op.f(f"ix_{table_prefix}users_email"),
        f"{table_prefix}users",
        ["email"],
        unique=False,
    )
    op.create_index(
        op.f(f"ix_{table_prefix}users_email_lower"),
        f"{table_prefix}users",
        ["email_lower"],
        unique=False,
    )
    op.create_index(
        op.f(f"ix_{table_prefix}users_email_verified"),
        f"{table_prefix}users",
        ["email_verified"],
        unique=False,
    )
    op.create_index(
        op.f(f"ix_{table_prefix}users_updated_at"),
        f"{table_prefix}users",
        ["updated_at"],
        unique=False,
    )

    if dialect == "postgresql":
        acr_enum = postgresql.ENUM(
            "0", "1", name=f"{table_prefix}acr", create_type=False
        )
        acr_enum.create(connection, checkfirst=True)
    else:
        acr_enum = sa.Enum("0", "1", name=f"{table_prefix}acr")

    op.create_table(
        f"{table_prefix}authorization_codes",
        sa.Column("code", sa.String(length=255), nullable=False),
        sa.Column("c_hash", sa.String(length=255), nullable=False),
        sa.Column("redirect_uri", sa.String(length=2048), nullable=False),
        sa.Column("scope", sa.JSON(), nullable=False),
        sa.Column(
            "authenticated_at",
            fief.models.generics.TIMESTAMPAware(timezone=True),
            nullable=False,
        ),
        sa.Column("nonce", sa.String(length=255), nullable=True),
        sa.Column("acr", acr_enum, nullable=False),
        sa.Column("code_challenge", sa.String(length=255), nullable=True),
        sa.Column("code_challenge_method", sa.String(length=255), nullable=True),
        sa.Column("user_id", fief.models.generics.GUID(), nullable=False),
        sa.Column("client_id", fief.models.generics.GUID(), nullable=False),
        sa.Column("id", fief.models.generics.GUID(), nullable=False),
        sa.Column(
            "created_at",
            fief.models.generics.TIMESTAMPAware(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            fief.models.generics.TIMESTAMPAware(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "expires_at",
            fief.models.generics.TIMESTAMPAware(timezone=True),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["client_id"], [f"{table_prefix}clients.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], [f"{table_prefix}users.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f(f"ix_{table_prefix}authorization_codes_code"),
        f"{table_prefix}authorization_codes",
        ["code"],
        unique=True,
    )
    op.create_index(
        op.f(f"ix_{table_prefix}authorization_codes_created_at"),
        f"{table_prefix}authorization_codes",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        op.f(f"ix_{table_prefix}authorization_codes_expires_at"),
        f"{table_prefix}authorization_codes",
        ["expires_at"],
        unique=False,
    )
    op.create_index(
        op.f(f"ix_{table_prefix}authorization_codes_updated_at"),
        f"{table_prefix}authorization_codes",
        ["updated_at"],
        unique=False,
    )
    op.create_table(
        f"{table_prefix}email_verifications",
        sa.Column("code", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("user_id", fief.models.generics.GUID(), nullable=False),
        sa.Column("id", fief.models.generics.GUID(), nullable=False),
        sa.Column(
            "created_at",
            fief.models.generics.TIMESTAMPAware(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            fief.models.generics.TIMESTAMPAware(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "expires_at",
            fief.models.generics.TIMESTAMPAware(timezone=True),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], [f"{table_prefix}users.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f(f"ix_{table_prefix}email_verifications_code"),
        f"{table_prefix}email_verifications",
        ["code"],
        unique=True,
    )
    op.create_index(
        op.f(f"ix_{table_prefix}email_verifications_created_at"),
        f"{table_prefix}email_verifications",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        op.f(f"ix_{table_prefix}email_verifications_email"),
        f"{table_prefix}email_verifications",
        ["email"],
        unique=False,
    )
    op.create_index(
        op.f(f"ix_{table_prefix}email_verifications_expires_at"),
        f"{table_prefix}email_verifications",
        ["expires_at"],
        unique=False,
    )
    op.create_index(
        op.f(f"ix_{table_prefix}email_verifications_updated_at"),
        f"{table_prefix}email_verifications",
        ["updated_at"],
        unique=False,
    )
    op.create_table(
        f"{table_prefix}grants",
        sa.Column("scope", sa.JSON(), nullable=False),
        sa.Column("user_id", fief.models.generics.GUID(), nullable=False),
        sa.Column("client_id", fief.models.generics.GUID(), nullable=False),
        sa.Column("id", fief.models.generics.GUID(), nullable=False),
        sa.Column(
            "created_at",
            fief.models.generics.TIMESTAMPAware(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            fief.models.generics.TIMESTAMPAware(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["client_id"], [f"{table_prefix}clients.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], [f"{table_prefix}users.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "client_id"),
    )
    op.create_index(
        op.f(f"ix_{table_prefix}grants_created_at"),
        f"{table_prefix}grants",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        op.f(f"ix_{table_prefix}grants_updated_at"),
        f"{table_prefix}grants",
        ["updated_at"],
        unique=False,
    )
    op.create_table(
        f"{table_prefix}login_sessions",
        sa.Column("token", sa.String(length=255), nullable=False),
        sa.Column("response_type", sa.String(length=255), nullable=False),
        sa.Column("response_mode", sa.String(length=255), nullable=False),
        sa.Column("redirect_uri", sa.String(length=2048), nullable=False),
        sa.Column("scope", sa.JSON(), nullable=False),
        sa.Column("prompt", sa.String(length=255), nullable=True),
        sa.Column("state", sa.String(length=2048), nullable=True),
        sa.Column("nonce", sa.String(length=255), nullable=True),
        sa.Column("acr", acr_enum, nullable=False),
        sa.Column("code_challenge", sa.String(length=255), nullable=True),
        sa.Column("code_challenge_method", sa.String(length=255), nullable=True),
        sa.Column("client_id", fief.models.generics.GUID(), nullable=False),
        sa.Column("id", fief.models.generics.GUID(), nullable=False),
        sa.Column(
            "created_at",
            fief.models.generics.TIMESTAMPAware(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            fief.models.generics.TIMESTAMPAware(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "expires_at",
            fief.models.generics.TIMESTAMPAware(timezone=True),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["client_id"], [f"{table_prefix}clients.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f(f"ix_{table_prefix}login_sessions_created_at"),
        f"{table_prefix}login_sessions",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        op.f(f"ix_{table_prefix}login_sessions_expires_at"),
        f"{table_prefix}login_sessions",
        ["expires_at"],
        unique=False,
    )
    op.create_index(
        op.f(f"ix_{table_prefix}login_sessions_token"),
        f"{table_prefix}login_sessions",
        ["token"],
        unique=True,
    )
    op.create_index(
        op.f(f"ix_{table_prefix}login_sessions_updated_at"),
        f"{table_prefix}login_sessions",
        ["updated_at"],
        unique=False,
    )
    op.create_table(
        f"{table_prefix}oauth_accounts",
        sa.Column(
            "access_token", fief.crypto.encryption.StringEncryptedType(), nullable=False
        ),
        sa.Column(
            "expires_at",
            fief.models.generics.TIMESTAMPAware(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "refresh_token", fief.crypto.encryption.StringEncryptedType(), nullable=True
        ),
        sa.Column("account_id", sa.String(length=512), nullable=False),
        sa.Column("account_email", sa.String(length=512), nullable=True),
        sa.Column("oauth_provider_id", fief.models.generics.GUID(), nullable=False),
        sa.Column("user_id", fief.models.generics.GUID(), nullable=True),
        sa.Column("tenant_id", fief.models.generics.GUID(), nullable=False),
        sa.Column("id", fief.models.generics.GUID(), nullable=False),
        sa.Column(
            "created_at",
            fief.models.generics.TIMESTAMPAware(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            fief.models.generics.TIMESTAMPAware(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["oauth_provider_id"],
            [f"{table_prefix}oauth_providers.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"], [f"{table_prefix}tenants.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], [f"{table_prefix}users.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("oauth_provider_id", "user_id"),
    )
    op.create_index(
        op.f(f"ix_{table_prefix}oauth_accounts_account_id"),
        f"{table_prefix}oauth_accounts",
        ["account_id"],
        unique=False,
    )
    op.create_index(
        op.f(f"ix_{table_prefix}oauth_accounts_created_at"),
        f"{table_prefix}oauth_accounts",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        op.f(f"ix_{table_prefix}oauth_accounts_updated_at"),
        f"{table_prefix}oauth_accounts",
        ["updated_at"],
        unique=False,
    )
    op.create_table(
        f"{table_prefix}refresh_tokens",
        sa.Column("token", sa.String(length=255), nullable=False),
        sa.Column("scope", sa.JSON(), nullable=False),
        sa.Column(
            "authenticated_at",
            fief.models.generics.TIMESTAMPAware(timezone=True),
            nullable=False,
        ),
        sa.Column("user_id", fief.models.generics.GUID(), nullable=False),
        sa.Column("client_id", fief.models.generics.GUID(), nullable=False),
        sa.Column("id", fief.models.generics.GUID(), nullable=False),
        sa.Column(
            "created_at",
            fief.models.generics.TIMESTAMPAware(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            fief.models.generics.TIMESTAMPAware(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "expires_at",
            fief.models.generics.TIMESTAMPAware(timezone=True),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["client_id"], [f"{table_prefix}clients.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], [f"{table_prefix}users.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f(f"ix_{table_prefix}refresh_tokens_created_at"),
        f"{table_prefix}refresh_tokens",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        op.f(f"ix_{table_prefix}refresh_tokens_expires_at"),
        f"{table_prefix}refresh_tokens",
        ["expires_at"],
        unique=False,
    )
    op.create_index(
        op.f(f"ix_{table_prefix}refresh_tokens_token"),
        f"{table_prefix}refresh_tokens",
        ["token"],
        unique=True,
    )
    op.create_index(
        op.f(f"ix_{table_prefix}refresh_tokens_updated_at"),
        f"{table_prefix}refresh_tokens",
        ["updated_at"],
        unique=False,
    )
    op.create_table(
        f"{table_prefix}session_tokens",
        sa.Column("token", sa.String(length=255), nullable=False),
        sa.Column("user_id", fief.models.generics.GUID(), nullable=False),
        sa.Column("id", fief.models.generics.GUID(), nullable=False),
        sa.Column(
            "created_at",
            fief.models.generics.TIMESTAMPAware(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            fief.models.generics.TIMESTAMPAware(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "expires_at",
            fief.models.generics.TIMESTAMPAware(timezone=True),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], [f"{table_prefix}users.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f(f"ix_{table_prefix}session_tokens_created_at"),
        f"{table_prefix}session_tokens",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        op.f(f"ix_{table_prefix}session_tokens_expires_at"),
        f"{table_prefix}session_tokens",
        ["expires_at"],
        unique=False,
    )
    op.create_index(
        op.f(f"ix_{table_prefix}session_tokens_token"),
        f"{table_prefix}session_tokens",
        ["token"],
        unique=True,
    )
    op.create_index(
        op.f(f"ix_{table_prefix}session_tokens_updated_at"),
        f"{table_prefix}session_tokens",
        ["updated_at"],
        unique=False,
    )
    op.create_table(
        f"{table_prefix}user_field_values",
        sa.Column("value_string", sa.Text(), nullable=True),
        sa.Column("value_integer", sa.Integer(), nullable=True),
        sa.Column("value_boolean", sa.Boolean(), nullable=True),
        sa.Column("value_date", sa.Date(), nullable=True),
        sa.Column(
            "value_datetime",
            fief.models.generics.TIMESTAMPAware(timezone=True),
            nullable=True,
        ),
        sa.Column("value_json", sa.JSON(), nullable=True),
        sa.Column("user_id", fief.models.generics.GUID(), nullable=False),
        sa.Column("user_field_id", fief.models.generics.GUID(), nullable=False),
        sa.Column("id", fief.models.generics.GUID(), nullable=False),
        sa.Column(
            "created_at",
            fief.models.generics.TIMESTAMPAware(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            fief.models.generics.TIMESTAMPAware(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_field_id"], [f"{table_prefix}user_fields.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], [f"{table_prefix}users.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_field_id", "user_id"),
    )
    op.create_index(
        op.f(f"ix_{table_prefix}user_field_values_created_at"),
        f"{table_prefix}user_field_values",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        op.f(f"ix_{table_prefix}user_field_values_updated_at"),
        f"{table_prefix}user_field_values",
        ["updated_at"],
        unique=False,
    )
    op.create_table(
        f"{table_prefix}user_permissions",
        sa.Column("user_id", fief.models.generics.GUID(), nullable=False),
        sa.Column("permission_id", fief.models.generics.GUID(), nullable=False),
        sa.Column("from_role_id", fief.models.generics.GUID(), nullable=True),
        sa.Column("id", fief.models.generics.GUID(), nullable=False),
        sa.Column(
            "created_at",
            fief.models.generics.TIMESTAMPAware(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            fief.models.generics.TIMESTAMPAware(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["from_role_id"], [f"{table_prefix}roles.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["permission_id"], [f"{table_prefix}permissions.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], [f"{table_prefix}users.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "permission_id", "from_role_id"),
    )
    op.create_index(
        op.f(f"ix_{table_prefix}user_permissions_created_at"),
        f"{table_prefix}user_permissions",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        op.f(f"ix_{table_prefix}user_permissions_updated_at"),
        f"{table_prefix}user_permissions",
        ["updated_at"],
        unique=False,
    )
    op.create_table(
        f"{table_prefix}user_roles",
        sa.Column("user_id", fief.models.generics.GUID(), nullable=False),
        sa.Column("role_id", fief.models.generics.GUID(), nullable=False),
        sa.Column("id", fief.models.generics.GUID(), nullable=False),
        sa.Column(
            "created_at",
            fief.models.generics.TIMESTAMPAware(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            fief.models.generics.TIMESTAMPAware(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["role_id"], [f"{table_prefix}roles.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], [f"{table_prefix}users.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "role_id"),
    )
    op.create_index(
        op.f(f"ix_{table_prefix}user_roles_created_at"),
        f"{table_prefix}user_roles",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        op.f(f"ix_{table_prefix}user_roles_updated_at"),
        f"{table_prefix}user_roles",
        ["updated_at"],
        unique=False,
    )
    op.create_table(
        f"{table_prefix}oauth_sessions",
        sa.Column("token", sa.String(length=255), nullable=False),
        sa.Column("redirect_uri", sa.Text(), nullable=False),
        sa.Column("oauth_provider_id", fief.models.generics.GUID(), nullable=False),
        sa.Column("oauth_account_id", fief.models.generics.GUID(), nullable=True),
        sa.Column("tenant_id", fief.models.generics.GUID(), nullable=False),
        sa.Column("id", fief.models.generics.GUID(), nullable=False),
        sa.Column(
            "created_at",
            fief.models.generics.TIMESTAMPAware(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            fief.models.generics.TIMESTAMPAware(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "expires_at",
            fief.models.generics.TIMESTAMPAware(timezone=True),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["oauth_account_id"],
            [f"{table_prefix}oauth_accounts.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["oauth_provider_id"],
            [f"{table_prefix}oauth_providers.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"], [f"{table_prefix}tenants.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f(f"ix_{table_prefix}oauth_sessions_created_at"),
        f"{table_prefix}oauth_sessions",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        op.f(f"ix_{table_prefix}oauth_sessions_expires_at"),
        f"{table_prefix}oauth_sessions",
        ["expires_at"],
        unique=False,
    )
    op.create_index(
        op.f(f"ix_{table_prefix}oauth_sessions_token"),
        f"{table_prefix}oauth_sessions",
        ["token"],
        unique=True,
    )
    op.create_index(
        op.f(f"ix_{table_prefix}oauth_sessions_updated_at"),
        f"{table_prefix}oauth_sessions",
        ["updated_at"],
        unique=False,
    )
    op.create_table(
        f"{table_prefix}registration_sessions",
        sa.Column("token", sa.String(length=255), nullable=False),
        sa.Column("flow", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=True),
        sa.Column("oauth_account_id", fief.models.generics.GUID(), nullable=True),
        sa.Column("tenant_id", fief.models.generics.GUID(), nullable=False),
        sa.Column("id", fief.models.generics.GUID(), nullable=False),
        sa.Column(
            "created_at",
            fief.models.generics.TIMESTAMPAware(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            fief.models.generics.TIMESTAMPAware(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "expires_at",
            fief.models.generics.TIMESTAMPAware(timezone=True),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["oauth_account_id"],
            [f"{table_prefix}oauth_accounts.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"], [f"{table_prefix}tenants.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f(f"ix_{table_prefix}registration_sessions_created_at"),
        f"{table_prefix}registration_sessions",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        op.f(f"ix_{table_prefix}registration_sessions_expires_at"),
        f"{table_prefix}registration_sessions",
        ["expires_at"],
        unique=False,
    )
    op.create_index(
        op.f(f"ix_{table_prefix}registration_sessions_token"),
        f"{table_prefix}registration_sessions",
        ["token"],
        unique=True,
    )
    op.create_index(
        op.f(f"ix_{table_prefix}registration_sessions_updated_at"),
        f"{table_prefix}registration_sessions",
        ["updated_at"],
        unique=False,
    )
    # ### end Alembic commands ###


def downgrade():
    table_prefix = op.get_context().opts["table_prefix"]

    op.drop_index(
        op.f(f"ix_{table_prefix}registration_sessions_updated_at"),
        table_name=f"{table_prefix}registration_sessions",
    )
    op.drop_index(
        op.f(f"ix_{table_prefix}registration_sessions_token"),
        table_name=f"{table_prefix}registration_sessions",
    )
    op.drop_index(
        op.f(f"ix_{table_prefix}registration_sessions_expires_at"),
        table_name=f"{table_prefix}registration_sessions",
    )
    op.drop_index(
        op.f(f"ix_{table_prefix}registration_sessions_created_at"),
        table_name=f"{table_prefix}registration_sessions",
    )
    op.drop_table(f"{table_prefix}registration_sessions")
    op.drop_index(
        op.f(f"ix_{table_prefix}oauth_sessions_updated_at"),
        table_name=f"{table_prefix}oauth_sessions",
    )
    op.drop_index(
        op.f(f"ix_{table_prefix}oauth_sessions_token"),
        table_name=f"{table_prefix}oauth_sessions",
    )
    op.drop_index(
        op.f(f"ix_{table_prefix}oauth_sessions_expires_at"),
        table_name=f"{table_prefix}oauth_sessions",
    )
    op.drop_index(
        op.f(f"ix_{table_prefix}oauth_sessions_created_at"),
        table_name=f"{table_prefix}oauth_sessions",
    )
    op.drop_table(f"{table_prefix}oauth_sessions")
    op.drop_index(
        op.f(f"ix_{table_prefix}user_roles_updated_at"),
        table_name=f"{table_prefix}user_roles",
    )
    op.drop_index(
        op.f(f"ix_{table_prefix}user_roles_created_at"),
        table_name=f"{table_prefix}user_roles",
    )
    op.drop_table(f"{table_prefix}user_roles")
    op.drop_index(
        op.f(f"ix_{table_prefix}user_permissions_updated_at"),
        table_name=f"{table_prefix}user_permissions",
    )
    op.drop_index(
        op.f(f"ix_{table_prefix}user_permissions_created_at"),
        table_name=f"{table_prefix}user_permissions",
    )
    op.drop_table(f"{table_prefix}user_permissions")
    op.drop_index(
        op.f(f"ix_{table_prefix}user_field_values_updated_at"),
        table_name=f"{table_prefix}user_field_values",
    )
    op.drop_index(
        op.f(f"ix_{table_prefix}user_field_values_created_at"),
        table_name=f"{table_prefix}user_field_values",
    )
    op.drop_table(f"{table_prefix}user_field_values")
    op.drop_index(
        op.f(f"ix_{table_prefix}session_tokens_updated_at"),
        table_name=f"{table_prefix}session_tokens",
    )
    op.drop_index(
        op.f(f"ix_{table_prefix}session_tokens_token"),
        table_name=f"{table_prefix}session_tokens",
    )
    op.drop_index(
        op.f(f"ix_{table_prefix}session_tokens_expires_at"),
        table_name=f"{table_prefix}session_tokens",
    )
    op.drop_index(
        op.f(f"ix_{table_prefix}session_tokens_created_at"),
        table_name=f"{table_prefix}session_tokens",
    )
    op.drop_table(f"{table_prefix}session_tokens")
    op.drop_index(
        op.f(f"ix_{table_prefix}refresh_tokens_updated_at"),
        table_name=f"{table_prefix}refresh_tokens",
    )
    op.drop_index(
        op.f(f"ix_{table_prefix}refresh_tokens_token"),
        table_name=f"{table_prefix}refresh_tokens",
    )
    op.drop_index(
        op.f(f"ix_{table_prefix}refresh_tokens_expires_at"),
        table_name=f"{table_prefix}refresh_tokens",
    )
    op.drop_index(
        op.f(f"ix_{table_prefix}refresh_tokens_created_at"),
        table_name=f"{table_prefix}refresh_tokens",
    )
    op.drop_table(f"{table_prefix}refresh_tokens")
    op.drop_index(
        op.f(f"ix_{table_prefix}oauth_accounts_updated_at"),
        table_name=f"{table_prefix}oauth_accounts",
    )
    op.drop_index(
        op.f(f"ix_{table_prefix}oauth_accounts_created_at"),
        table_name=f"{table_prefix}oauth_accounts",
    )
    op.drop_index(
        op.f(f"ix_{table_prefix}oauth_accounts_account_id"),
        table_name=f"{table_prefix}oauth_accounts",
    )
    op.drop_table(f"{table_prefix}oauth_accounts")
    op.drop_index(
        op.f(f"ix_{table_prefix}login_sessions_updated_at"),
        table_name=f"{table_prefix}login_sessions",
    )
    op.drop_index(
        op.f(f"ix_{table_prefix}login_sessions_token"),
        table_name=f"{table_prefix}login_sessions",
    )
    op.drop_index(
        op.f(f"ix_{table_prefix}login_sessions_expires_at"),
        table_name=f"{table_prefix}login_sessions",
    )
    op.drop_index(
        op.f(f"ix_{table_prefix}login_sessions_created_at"),
        table_name=f"{table_prefix}login_sessions",
    )
    op.drop_table(f"{table_prefix}login_sessions")
    op.drop_index(
        op.f(f"ix_{table_prefix}grants_updated_at"), table_name=f"{table_prefix}grants"
    )
    op.drop_index(
        op.f(f"ix_{table_prefix}grants_created_at"), table_name=f"{table_prefix}grants"
    )
    op.drop_table(f"{table_prefix}grants")
    op.drop_index(
        op.f(f"ix_{table_prefix}email_verifications_updated_at"),
        table_name=f"{table_prefix}email_verifications",
    )
    op.drop_index(
        op.f(f"ix_{table_prefix}email_verifications_expires_at"),
        table_name=f"{table_prefix}email_verifications",
    )
    op.drop_index(
        op.f(f"ix_{table_prefix}email_verifications_email"),
        table_name=f"{table_prefix}email_verifications",
    )
    op.drop_index(
        op.f(f"ix_{table_prefix}email_verifications_created_at"),
        table_name=f"{table_prefix}email_verifications",
    )
    op.drop_index(
        op.f(f"ix_{table_prefix}email_verifications_code"),
        table_name=f"{table_prefix}email_verifications",
    )
    op.drop_table(f"{table_prefix}email_verifications")
    op.drop_index(
        op.f(f"ix_{table_prefix}authorization_codes_updated_at"),
        table_name=f"{table_prefix}authorization_codes",
    )
    op.drop_index(
        op.f(f"ix_{table_prefix}authorization_codes_expires_at"),
        table_name=f"{table_prefix}authorization_codes",
    )
    op.drop_index(
        op.f(f"ix_{table_prefix}authorization_codes_created_at"),
        table_name=f"{table_prefix}authorization_codes",
    )
    op.drop_index(
        op.f(f"ix_{table_prefix}authorization_codes_code"),
        table_name=f"{table_prefix}authorization_codes",
    )
    op.drop_table(f"{table_prefix}authorization_codes")
    op.drop_index(
        op.f(f"ix_{table_prefix}users_updated_at"), table_name=f"{table_prefix}users"
    )
    op.drop_index(
        op.f(f"ix_{table_prefix}users_email_verified"),
        table_name=f"{table_prefix}users",
    )
    op.drop_index(
        op.f(f"ix_{table_prefix}users_email_lower"), table_name=f"{table_prefix}users"
    )
    op.drop_index(
        op.f(f"ix_{table_prefix}users_email"), table_name=f"{table_prefix}users"
    )
    op.drop_index(
        op.f(f"ix_{table_prefix}users_created_at"), table_name=f"{table_prefix}users"
    )
    op.drop_table(f"{table_prefix}users")
    op.drop_table(f"{table_prefix}tenants_oauth_providers")
    op.drop_index(
        op.f(f"ix_{table_prefix}clients_updated_at"),
        table_name=f"{table_prefix}clients",
    )
    op.drop_index(
        op.f(f"ix_{table_prefix}clients_created_at"),
        table_name=f"{table_prefix}clients",
    )
    op.drop_index(
        op.f(f"ix_{table_prefix}clients_client_secret"),
        table_name=f"{table_prefix}clients",
    )
    op.drop_index(
        op.f(f"ix_{table_prefix}clients_client_id"), table_name=f"{table_prefix}clients"
    )
    op.drop_table(f"{table_prefix}clients")
    op.drop_index(
        op.f(f"ix_{table_prefix}webhook_logs_updated_at"),
        table_name=f"{table_prefix}webhook_logs",
    )
    op.drop_index(
        op.f(f"ix_{table_prefix}webhook_logs_created_at"),
        table_name=f"{table_prefix}webhook_logs",
    )
    op.drop_table(f"{table_prefix}webhook_logs")
    op.drop_index(
        op.f(f"ix_{table_prefix}tenants_updated_at"),
        table_name=f"{table_prefix}tenants",
    )
    op.drop_index(
        op.f(f"ix_{table_prefix}tenants_created_at"),
        table_name=f"{table_prefix}tenants",
    )
    op.drop_table(f"{table_prefix}tenants")
    op.drop_table(f"{table_prefix}roles_permissions")
    op.drop_index(
        op.f(f"ix_{table_prefix}webhooks_updated_at"),
        table_name=f"{table_prefix}webhooks",
    )
    op.drop_index(
        op.f(f"ix_{table_prefix}webhooks_created_at"),
        table_name=f"{table_prefix}webhooks",
    )
    op.drop_table(f"{table_prefix}webhooks")
    op.drop_index(
        op.f(f"ix_{table_prefix}user_fields_updated_at"),
        table_name=f"{table_prefix}user_fields",
    )
    op.drop_index(
        op.f(f"ix_{table_prefix}user_fields_type"),
        table_name=f"{table_prefix}user_fields",
    )
    op.drop_index(
        op.f(f"ix_{table_prefix}user_fields_slug"),
        table_name=f"{table_prefix}user_fields",
    )
    op.drop_index(
        op.f(f"ix_{table_prefix}user_fields_created_at"),
        table_name=f"{table_prefix}user_fields",
    )
    op.drop_table(f"{table_prefix}user_fields")
    op.drop_index(
        op.f(f"ix_{table_prefix}themes_updated_at"), table_name=f"{table_prefix}themes"
    )
    op.drop_index(
        op.f(f"ix_{table_prefix}themes_created_at"), table_name=f"{table_prefix}themes"
    )
    op.drop_table(f"{table_prefix}themes")
    op.drop_index(
        op.f(f"ix_{table_prefix}roles_updated_at"), table_name=f"{table_prefix}roles"
    )
    op.drop_index(
        op.f(f"ix_{table_prefix}roles_created_at"), table_name=f"{table_prefix}roles"
    )
    op.drop_table(f"{table_prefix}roles")
    op.drop_index(
        op.f(f"ix_{table_prefix}permissions_updated_at"),
        table_name=f"{table_prefix}permissions",
    )
    op.drop_index(
        op.f(f"ix_{table_prefix}permissions_created_at"),
        table_name=f"{table_prefix}permissions",
    )
    op.drop_table(f"{table_prefix}permissions")
    op.drop_index(
        op.f(f"ix_{table_prefix}oauth_providers_updated_at"),
        table_name=f"{table_prefix}oauth_providers",
    )
    op.drop_index(
        op.f(f"ix_{table_prefix}oauth_providers_created_at"),
        table_name=f"{table_prefix}oauth_providers",
    )
    op.drop_table(f"{table_prefix}oauth_providers")
    op.drop_index(
        op.f(f"ix_{table_prefix}email_templates_updated_at"),
        table_name=f"{table_prefix}email_templates",
    )
    op.drop_index(
        op.f(f"ix_{table_prefix}email_templates_created_at"),
        table_name=f"{table_prefix}email_templates",
    )
    op.drop_table(f"{table_prefix}email_templates")
    op.drop_index(
        op.f(f"ix_{table_prefix}email_domains_updated_at"),
        table_name=f"{table_prefix}email_domains",
    )
    op.drop_index(
        op.f(f"ix_{table_prefix}email_domains_created_at"),
        table_name=f"{table_prefix}email_domains",
    )
    op.drop_table(f"{table_prefix}email_domains")
    op.drop_index(
        op.f(f"ix_{table_prefix}audit_logs_timestamp"),
        table_name=f"{table_prefix}audit_logs",
    )
    op.drop_index(
        op.f(f"ix_{table_prefix}audit_logs_subject_user_id"),
        table_name=f"{table_prefix}audit_logs",
    )
    op.drop_index(
        op.f(f"ix_{table_prefix}audit_logs_object_id"),
        table_name=f"{table_prefix}audit_logs",
    )
    op.drop_index(
        op.f(f"ix_{table_prefix}audit_logs_object_class"),
        table_name=f"{table_prefix}audit_logs",
    )
    op.drop_index(
        op.f(f"ix_{table_prefix}audit_logs_level"),
        table_name=f"{table_prefix}audit_logs",
    )
    op.drop_index(
        op.f(f"ix_{table_prefix}audit_logs_admin_user_id"),
        table_name=f"{table_prefix}audit_logs",
    )
    op.drop_index(
        op.f(f"ix_{table_prefix}audit_logs_admin_api_key_id"),
        table_name=f"{table_prefix}audit_logs",
    )
    op.drop_table(f"{table_prefix}audit_logs")
    # ### end Alembic commands ###
