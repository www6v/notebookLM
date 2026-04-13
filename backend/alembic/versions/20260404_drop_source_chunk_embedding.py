"""Drop unused source_chunks.embedding column.

Revision ID: 20260404_drop_source_chunk_embedding
Revises: 20260404_slide_audience
Create Date: 2026-04-04
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260404_drop_source_chunk_embedding"
down_revision = "20260404_slide_audience"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column("source_chunks", "embedding")


def downgrade() -> None:
    op.add_column(
        "source_chunks",
        sa.Column("embedding", sa.Text(), nullable=True),
    )
