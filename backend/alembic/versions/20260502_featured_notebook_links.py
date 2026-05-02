"""Add featured_notebook_links for home Featured tab.

Revision ID: 20260502_featured_nb
Revises: 20260419_system_settings
Create Date: 2026-05-02

"""
import uuid
from datetime import datetime

from alembic import op
import sqlalchemy as sa


revision = "20260502_featured_nb"
down_revision = "20260419_system_settings"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "featured_notebook_links",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("share_token", sa.String(length=64), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("custom_title", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("share_token"),
    )
    op.create_index(
        "ix_featured_notebook_links_sort_order",
        "featured_notebook_links",
        ["sort_order"],
        unique=False,
    )
    now = datetime.utcnow()
    demo_token = "xHlLsvQ3aoSoghb_truoamdecqQKS9Sb7til-osh8C8"
    conn = op.get_bind()
    conn.execute(
        sa.text(
            """
            INSERT INTO featured_notebook_links
            (id, share_token, sort_order, custom_title, created_at, updated_at)
            VALUES (:id, :token, 0, NULL, :ts, :ts)
            """
        ),
        {
            "id": str(uuid.uuid4()),
            "token": demo_token,
            "ts": now,
        },
    )


def downgrade() -> None:
    op.drop_index(
        "ix_featured_notebook_links_sort_order",
        table_name="featured_notebook_links",
    )
    op.drop_table("featured_notebook_links")
