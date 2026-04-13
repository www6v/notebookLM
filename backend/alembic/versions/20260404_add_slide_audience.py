"""Add slide_audience to slide_decks.

Revision ID: 20260404_slide_audience
Revises: 20260401_infographic_visual_style
Create Date: 2026-04-04
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260404_slide_audience"
down_revision = "20260401_infographic_visual_style"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "slide_decks",
        sa.Column(
            "slide_audience",
            sa.String(length=50),
            nullable=False,
            server_default="general",
        ),
    )


def downgrade() -> None:
    op.drop_column("slide_decks", "slide_audience")
