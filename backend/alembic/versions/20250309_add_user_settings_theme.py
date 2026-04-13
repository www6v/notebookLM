"""Add theme (website mode) to user_settings.

Revision ID: 20250309_user_settings_theme
Revises: 20250303_raw_content_longtext
Create Date: 2025-03-09

"""
from alembic import op
import sqlalchemy as sa


revision = '20250309_user_settings_theme'
down_revision = '20250303_raw_content_longtext'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'user_settings',
        sa.Column(
            'theme',
            sa.String(10),
            nullable=False,
            server_default='light',
        ),
    )


def downgrade() -> None:
    op.drop_column('user_settings', 'theme')
