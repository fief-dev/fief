"""Remove index on AuditLog.message

Revision ID: aa662768d69b
Revises: 2501f74d0c55
Create Date: 2022-11-29 09:31:08.396676

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy import exc

import fief

# revision identifiers, used by Alembic.
revision = "aa662768d69b"
down_revision = "2501f74d0c55"
branch_labels = None
depends_on = None


def upgrade():
    """
    On older versions of Fief, we created an index on AuditLog.message.
    It provoked the bug fief-dev/fief#115 on MySQL.

    We removed its creation in the existing migration, but we still need
    to remove it from existing DB, if it exists.
    """
    bind = op.get_context().bind
    inspector = sa.inspect(bind)
    indexes = inspector.get_indexes("fief_audit_logs")
    for index in indexes:
        if index["name"] == "ix_fief_audit_logs_message":
            op.drop_index("ix_fief_audit_logs_message", table_name="fief_audit_logs")
            break


def downgrade():
    pass
