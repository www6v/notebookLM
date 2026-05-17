"""Add open_api_credentials for OpenClaw agent access.

Revision ID: 20260517_open_api_cred
Revises: 20260511_discover_sub
Create Date: 2026-05-17

"""
from alembic import op
import sqlalchemy as sa


revision = "20260517_open_api_cred"
down_revision = "20260511_discover_sub"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "open_api_credentials",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("client_id", sa.String(64), nullable=False, unique=True),
        sa.Column("api_key_hash", sa.String(255), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index(
        "ix_open_api_credentials_client_id",
        "open_api_credentials",
        ["client_id"],
        unique=True,
    )
    op.create_index(
        "ix_open_api_credentials_user_id",
        "open_api_credentials",
        ["user_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_open_api_credentials_user_id", "open_api_credentials")
    op.drop_index("ix_open_api_credentials_client_id", "open_api_credentials")
    op.drop_table("open_api_credentials")
