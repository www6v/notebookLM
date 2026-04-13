"""Add podcast_overviews table for audio overview studio output.

Revision ID: 20260405_podcast_overviews
Revises: 20260404_drop_source_chunk_embedding
Create Date: 2026-04-05
"""

from alembic import op
import sqlalchemy as sa


revision = "20260405_podcast_overviews"
down_revision = "20260404_drop_source_chunk_embedding"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "podcast_overviews",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("notebook_id", sa.String(length=36), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("suggested_filename", sa.String(length=255), nullable=True),
        sa.Column("audio_format", sa.String(length=50), nullable=False),
        sa.Column("audio_language", sa.String(length=50), nullable=False),
        sa.Column("audio_length", sa.String(length=50), nullable=False),
        sa.Column("audio_focus_prompt", sa.Text(), nullable=True),
        sa.Column("file_path", sa.String(length=500), nullable=True),
        sa.Column("transcript", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("source_count", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["notebook_id"],
            ["notebooks.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("podcast_overviews")
