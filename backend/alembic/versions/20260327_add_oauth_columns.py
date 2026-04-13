"""Add OAuth columns to users; allow nullable password_hash for OAuth users.

Revision ID: 20260327_oauth
Revises: 20260319_dr
Create Date: 2026-03-27
"""

from alembic import op
import sqlalchemy as sa


revision = "20260327_oauth"
down_revision = "20260319_dr"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("oauth_provider", sa.String(32), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column("oauth_subject", sa.String(255), nullable=True),
    )
    op.alter_column(
        "users",
        "password_hash",
        existing_type=sa.String(255),
        nullable=True,
    )
    op.create_index(
        "uq_users_oauth_provider_subject",
        "users",
        ["oauth_provider", "oauth_subject"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("uq_users_oauth_provider_subject", table_name="users")
    op.alter_column(
        "users",
        "password_hash",
        existing_type=sa.String(255),
        nullable=False,
    )
    op.drop_column("users", "oauth_subject")
    op.drop_column("users", "oauth_provider")
