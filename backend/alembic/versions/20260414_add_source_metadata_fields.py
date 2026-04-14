"""Add summary and tags fields on sources for metadata skill.

Revision ID: 20260414_source_metadata_fields
Revises: 20260408_notebook_share_token
Create Date: 2026-04-14
"""

from alembic import op
from sqlalchemy.dialects.mysql import JSON, LONGTEXT
import sqlalchemy as sa


revision = "20260414_source_metadata_fields"
down_revision = "20260408_notebook_share_token"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "sources",
        sa.Column("summary", LONGTEXT(), nullable=True),
    )
    op.add_column(
        "sources",
        sa.Column("tags", JSON(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("sources", "tags")
    op.drop_column("sources", "summary")
