"""Add UserField model

Revision ID: b530ce0d8bd9
Revises: bc4021719fac
Create Date: 2022-04-28 15:35:51.333535

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

import fief

# revision identifiers, used by Alembic.
revision = "b530ce0d8bd9"
down_revision = "bc4021719fac"
branch_labels = None
depends_on = None


def upgrade():
    connection = op.get_bind()
    if connection.dialect.name == "postgresql":
        client_type_enum = postgresql.ENUM(
            "STRING",
            "INTEGER",
            "BOOLEAN",
            "DATE",
            "DATETIME",
            "CHOICE",
            "PHONE_NUMBER",
            "ADDRESS",
            "TIMEZONE",
            name="userfieldtype",
            create_type=False,
        )
        client_type_enum.create(connection, checkfirst=True)
    else:
        client_type_enum = sa.Enum(
            "STRING",
            "INTEGER",
            "BOOLEAN",
            "DATE",
            "DATETIME",
            "CHOICE",
            "PHONE_NUMBER",
            "ADDRESS",
            "TIMEZONE",
            name="userfieldtype",
        )

    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "fief_user_fields",
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
        sa.Column("name", sa.String(length=320), nullable=False),
        sa.Column("slug", sa.String(length=320), nullable=False),
        sa.Column(
            "type",
            client_type_enum,
            nullable=True,
        ),
        sa.Column("configuration", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_fief_user_fields_created_at"),
        "fief_user_fields",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_fief_user_fields_slug"), "fief_user_fields", ["slug"], unique=True
    )
    op.create_index(
        op.f("ix_fief_user_fields_type"), "fief_user_fields", ["type"], unique=False
    )
    op.create_index(
        op.f("ix_fief_user_fields_updated_at"),
        "fief_user_fields",
        ["updated_at"],
        unique=False,
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f("ix_fief_user_fields_updated_at"), table_name="fief_user_fields")
    op.drop_index(op.f("ix_fief_user_fields_type"), table_name="fief_user_fields")
    op.drop_index(op.f("ix_fief_user_fields_slug"), table_name="fief_user_fields")
    op.drop_index(op.f("ix_fief_user_fields_created_at"), table_name="fief_user_fields")
    op.drop_table("fief_user_fields")

    try:
        client_type_enum = postgresql.ENUM(
            "STRING",
            "INTEGER",
            "BOOLEAN",
            "DATE",
            "DATETIME",
            "CHOICE",
            "PHONE_NUMBER",
            "ADDRESS",
            "TIMEZONE",
            name="userfieldtype",
            create_type=False,
        )
        client_type_enum.drop(op.get_bind(), checkfirst=True)
    except AttributeError:
        pass
    # ### end Alembic commands ###
