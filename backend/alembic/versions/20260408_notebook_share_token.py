"""Add share_token on notebooks for public read-only links.

Revision ID: 20260408_notebook_share_token
Revises: 20260406_dr_celery_id
Create Date: 2026-04-08
"""

from alembic import op
import sqlalchemy as sa


revision = "20260408_notebook_share_token"
down_revision = "20260406_dr_celery_id"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "notebooks",
        sa.Column("share_token", sa.String(length=64), nullable=True),
    )
    op.create_index(
        "ix_notebooks_share_token",
        "notebooks",
        ["share_token"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("ix_notebooks_share_token", table_name="notebooks")
    op.drop_column("notebooks", "share_token")
