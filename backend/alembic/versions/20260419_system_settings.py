"""Add system_settings for fleet-wide client config.

Revision ID: 20260419_system_settings
Revises: 20260414_source_metadata_fields
Create Date: 2026-04-19

"""
from alembic import op
import sqlalchemy as sa


revision = '20260419_system_settings'
down_revision = '20260414_source_metadata_fields'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'system_settings',
        sa.Column('key', sa.String(100), primary_key=True),
        sa.Column('value', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('system_settings')
