"""Add deep_research_reports table for DeerFlow Deep Research.

Revision ID: 20260319_dr
Revises: 20260317a
Create Date: 2026-03-19

"""

from alembic import op
import sqlalchemy as sa


revision = "20260319_dr"
down_revision = "20260317a"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "deep_research_reports",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "notebook_id",
            sa.String(36),
            sa.ForeignKey("notebooks.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("query", sa.String(1000), nullable=False),
        sa.Column(
            "status",
            sa.String(50),
            nullable=False,
            server_default="pending",
        ),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column(
            "source_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "popular_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column("deer_flow_thread_id", sa.String(64), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("deep_research_reports")
