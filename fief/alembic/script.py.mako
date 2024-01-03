"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

import fief

# revision identifiers, used by Alembic.
revision = ${repr(up_revision)}
down_revision = ${repr(down_revision)}
branch_labels = ${repr(branch_labels)}
depends_on = ${repr(depends_on)}


def upgrade():
    table_prefix = op.get_context().opts["table_prefix"]
    ${upgrades if upgrades else "pass"}


def downgrade():
    table_prefix = op.get_context().opts["table_prefix"]
    ${downgrades if downgrades else "pass"}
