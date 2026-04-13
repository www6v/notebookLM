"""Add file_size_bytes on sources for upload size tracking.

Revision ID: 20260405_source_file_size_bytes
Revises: 20260405_podcast_overviews
Create Date: 2026-04-05
"""

from alembic import op
import sqlalchemy as sa


revision = "20260405_source_file_size_bytes"
down_revision = "20260405_podcast_overviews"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "sources",
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("sources", "file_size_bytes")
