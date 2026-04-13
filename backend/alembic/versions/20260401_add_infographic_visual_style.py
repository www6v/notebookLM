"""Add infographic_visual_style to infographics.

Revision ID: 20260401_infographic_visual_style
Revises: 20260329_studio_errors
Create Date: 2026-04-01

"""
from alembic import op
import sqlalchemy as sa


revision = "20260401_infographic_visual_style"
down_revision = "20260329_studio_errors"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "infographics",
        sa.Column(
            "infographic_visual_style",
            sa.String(length=50),
            nullable=False,
            server_default="craft-handmade",
        ),
    )


def downgrade() -> None:
    op.drop_column("infographics", "infographic_visual_style")
