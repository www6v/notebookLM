"""Add role and is_active columns to users table.

Revision ID: 20250315_user_role
Revises: 20250315_source_count
Create Date: 2025-03-15

"""
from alembic import op
import sqlalchemy as sa


revision = '20250315_user_role'
down_revision = '20250315_source_count'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'users',
        sa.Column(
            'role', sa.String(20), nullable=False, server_default='free'
        ),
    )
    op.add_column(
        'users',
        sa.Column(
            'is_active', sa.Boolean(), nullable=False, server_default='1'
        ),
    )


def downgrade() -> None:
    op.drop_column('users', 'is_active')
    op.drop_column('users', 'role')
