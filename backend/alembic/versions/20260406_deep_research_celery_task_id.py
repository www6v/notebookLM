"""Add celery_task_id on deep_research_reports for cancel/revoke.

Revision ID: 20260406_dr_celery_id
Revises: 20260405_source_file_size_bytes
Create Date: 2026-04-06
"""

from alembic import op
import sqlalchemy as sa


revision = "20260406_dr_celery_id"
down_revision = "20260405_source_file_size_bytes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "deep_research_reports",
        sa.Column("celery_task_id", sa.String(255), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("deep_research_reports", "celery_task_id")
