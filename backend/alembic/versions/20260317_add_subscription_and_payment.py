"""Add subscription fields to users and create payment_orders table.

Revision ID: 20260317a
Revises: 20250315_add_studio_source_count
Create Date: 2026-03-17
"""

from alembic import op
import sqlalchemy as sa

revision = "20260317a"
down_revision = "20250315_user_role"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("subscription_expires_at", sa.DateTime(), nullable=True),
    )
    op.add_column(
        "users",
        sa.Column(
            "subscription_plan",
            sa.String(20),
            nullable=False,
            server_default="free",
        ),
    )

    op.create_table(
        "payment_orders",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("out_trade_no", sa.String(64), unique=True, nullable=False, index=True),
        sa.Column("pay_channel", sa.String(20), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("plan", sa.String(20), nullable=False, server_default="paid"),
        sa.Column("duration_months", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("trade_no", sa.String(128), nullable=True),
        sa.Column("paid_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("payment_orders")
    op.drop_column("users", "subscription_plan")
    op.drop_column("users", "subscription_expires_at")
