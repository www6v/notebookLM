"""Add error_message columns for studio outputs.

Revision ID: 20260329_studio_errors
Revises: 20260327_oauth
Create Date: 2026-03-29
"""

from alembic import op
import sqlalchemy as sa


revision = "20260329_studio_errors"
down_revision = "20260327_oauth"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "mind_maps",
        sa.Column("error_message", sa.Text(), nullable=True),
    )
    op.add_column(
        "slide_decks",
        sa.Column("error_message", sa.Text(), nullable=True),
    )
    op.add_column(
        "infographics",
        sa.Column("error_message", sa.Text(), nullable=True),
    )
    op.add_column(
        "reports",
        sa.Column("error_message", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("reports", "error_message")
    op.drop_column("infographics", "error_message")
    op.drop_column("slide_decks", "error_message")
    op.drop_column("mind_maps", "error_message")
