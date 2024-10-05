"""Add unique constraint on OAuthAccount provider_id and account_id

Revision ID: a736fe95ec4f
Revises: 6d9fa141730c
Create Date: 2024-08-29 09:01:04.397106

"""

import sqlalchemy as sa
from alembic import op

import fief

# revision identifiers, used by Alembic.
revision = "a736fe95ec4f"
down_revision = "6d9fa141730c"
branch_labels = None
depends_on = None


def upgrade():
    table_prefix = op.get_context().opts["table_prefix"]
    # ### commands auto generated by Alembic - please adjust! ###
    op.execute(
        f"""
        DELETE FROM {table_prefix}oauth_accounts
        WHERE user_id IS NULL
        """
    )

    connection = op.get_bind()
    if connection.dialect.name == "sqlite":
        with op.batch_alter_table(f"{table_prefix}oauth_accounts") as batch_op:
            batch_op.create_unique_constraint(
                op.f(f"{table_prefix}oauth_accounts_oauth_provider_id_account_id_key"),
                ["oauth_provider_id", "account_id"],
            )
    else:
        op.create_unique_constraint(
            op.f(f"{table_prefix}oauth_accounts_oauth_provider_id_account_id_key"),
            f"{table_prefix}oauth_accounts",
            ["oauth_provider_id", "account_id"],
        )
    # ### end Alembic commands ###


def downgrade():
    table_prefix = op.get_context().opts["table_prefix"]
    # ### commands auto generated by Alembic - please adjust! ###

    connection = op.get_bind()
    if connection.dialect.name == "sqlite":
        with op.batch_alter_table(f"{table_prefix}oauth_accounts") as batch_op:
            batch_op.drop_constraint(
                op.f(f"{table_prefix}oauth_accounts_oauth_provider_id_account_id_key"),
                type_="unique",
            )
    else:
        op.drop_constraint(
            op.f(f"{table_prefix}oauth_accounts_oauth_provider_id_account_id_key"),
            f"{table_prefix}oauth_accounts",
            type_="unique",
        )
    # ### end Alembic commands ###