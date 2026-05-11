"""Add notebook_discover_profiles and notebook_subscriptions.

Revision ID: 20260511_discover_sub
Revises: 20260502_featured_nb
Create Date: 2026-05-11

"""

from alembic import op
import sqlalchemy as sa


revision = "20260511_discover_sub"
down_revision = "20260502_featured_nb"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "notebook_discover_profiles",
        sa.Column("notebook_id", sa.String(length=36), nullable=False),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("cover_url", sa.String(length=512), nullable=False),
        sa.Column("subscriber_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("notebook_id"),
    )
    op.create_table(
        "notebook_subscriptions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("subscriber_user_id", sa.String(length=36), nullable=False),
        sa.Column("notebook_id", sa.String(length=36), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "subscriber_user_id",
            "notebook_id",
            name="uq_sub_notebook",
        ),
    )
    op.create_index(
        "ix_notebook_subscriptions_notebook_id",
        "notebook_subscriptions",
        ["notebook_id"],
        unique=False,
    )
    op.create_index(
        "ix_notebook_subscriptions_subscriber_user_id",
        "notebook_subscriptions",
        ["subscriber_user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_notebook_subscriptions_subscriber_user_id",
        table_name="notebook_subscriptions",
    )
    op.drop_index(
        "ix_notebook_subscriptions_notebook_id",
        table_name="notebook_subscriptions",
    )
    op.drop_table("notebook_subscriptions")
    op.drop_table("notebook_discover_profiles")
