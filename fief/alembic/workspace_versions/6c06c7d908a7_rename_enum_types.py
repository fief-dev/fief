"""Rename enum types

Revision ID: 6c06c7d908a7
Revises: 676305863b8f
Create Date: 2023-08-29 11:04:16.791263

"""
import sqlalchemy as sa
from alembic import op

import fief

# revision identifiers, used by Alembic.
revision = "6c06c7d908a7"
down_revision = "676305863b8f"
branch_labels = None
depends_on = None


def upgrade():
    connection = op.get_bind()
    dialect = connection.dialect.name

    if dialect == "postgresql":
        op.execute("ALTER TYPE acr RENAME TO fief_acr")
        op.execute("ALTER TYPE userfieldtype RENAME TO fief_userfieldtype")
        op.execute("ALTER TYPE clienttype RENAME TO fief_clienttype")


def downgrade():
    connection = op.get_bind()
    dialect = connection.dialect.name

    if dialect == "postgresql":
        op.execute("ALTER TYPE fief_acr RENAME TO acr")
        op.execute("ALTER TYPE fief_userfieldtype RENAME TO userfieldtype")
        op.execute("ALTER TYPE fief_clienttype RENAME TO clienttype")
