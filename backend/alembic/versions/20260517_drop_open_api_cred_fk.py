"""Drop open_api_credentials.user_id FK (app-level integrity).

Revision ID: 20260517_open_api_no_fk
Revises: 20260517_open_api_cred
Create Date: 2026-05-17

"""

import sqlalchemy as sa
from alembic import op


revision = "20260517_open_api_no_fk"
down_revision = "20260517_open_api_cred"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = sa.inspect(bind)
    for fk in insp.get_foreign_keys("open_api_credentials"):
        if fk.get("referred_table") == "users":
            op.drop_constraint(
                fk["name"],
                "open_api_credentials",
                type_="foreignkey",
            )


def downgrade() -> None:
    op.create_foreign_key(
        "fk_open_api_credentials_user_id",
        "open_api_credentials",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )
